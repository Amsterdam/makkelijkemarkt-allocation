from collections import deque
from operator import attrgetter, sub

from v2.conf import TraceMixin, Status, ALL_VPH_STATUS, PhaseValue
from v2.allocations.vpl import VplAllocation
from v2.allocations.soll import SollAllocation


class BaseStrategy(TraceMixin):
    def __init__(self, markt, **filter_kwargs):
        self.markt = markt
        self.working_copies = []
        self.ondernemer_filter_kwargs = filter_kwargs
        self.kramen_filter_kwargs = filter_kwargs
        self.trace.set_cycle()

    def log_rejections(self):
        ondernemers = self.markt.ondernemers.select(**self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            if ondernemer.is_rejected:
                log_entry = {
                    'rank': ondernemer.rank,
                    'reason': ondernemer.reject_reason,
                    'reason_detail': ondernemer.reject_reason.value,
                }
                self.markt.rejection_log.append(log_entry)

    def set_ondernemer_filter_kwargs(self, **filter_kwargs):
        self.ondernemer_filter_kwargs = filter_kwargs

    def set_kramen_filter_kwargs(self, **filter_kwargs):
        self.kramen_filter_kwargs = filter_kwargs

    def is_iteration_better_than_previous(self):
        if self.working_copies:
            previous = self.working_copies[-1]
            _, previous_ondernemers, *_ = previous
            combined_ondernemers = list(zip(self.markt.ondernemers.ondernemers, previous_ondernemers.ondernemers))
            less_kramen = []
            for current, previous in combined_ondernemers:
                delta = len(current.kramen) - len(previous.kramen)
                if delta < 0:
                    if current.status == Status.SOLL:
                        if not current.anywhere:
                            continue
                        if len(current.kramen) + 1 >= self.markt.kramen_per_ondernemer:
                            continue
                    if current.status == Status.B_LIST:
                        continue
                    self.trace.debug(f"Ondernemer has less kramen in current iteration than previous")
                    self.trace.debug(f"current: {current}")
                    self.trace.debug(f"previous: {previous}")
                    less_kramen.append([current, previous])
            if less_kramen:
                return False
            return True

    def is_allocation_valid(self):
        return (self.is_iteration_better_than_previous() and
                self.markt.is_allocation_valid(**self.ondernemer_filter_kwargs))

    def kramen_still_available(self):
        available_kramen_count = self.markt.kramen.find_clusters(1, **self.kramen_filter_kwargs)
        self.trace.debug(f"Available kramen: {available_kramen_count}")
        return available_kramen_count

    def run(self):
        raise NotImplementedError

    def should_allocation_loop_continue(self):
        if self.markt.is_allocation_hash_same_as_previous_round():
            self.trace.debug('SAME HASH')
            return False

        if not self.is_allocation_valid():
            if self.markt.kramen_per_ondernemer > 1:
                self.markt.restore_working_copy(self.working_copies[-1])  # fallback to the previous state
            return False

        if not self.kramen_still_available():
            return False

        self.working_copies.append(self.markt.get_working_copy())
        self.markt.kramen_per_ondernemer += 1
        return True

    def finish(self):
        self.markt.report_indeling()
        self.log_rejections()
        self.markt.clear_allocation_hashes()
        self.markt.report_ondernemers(**self.ondernemer_filter_kwargs)
        self.trace.set_cycle()


class ReceiveOwnKramenStrategy(BaseStrategy):
    def run(self):
        vpl_allocation = VplAllocation(self.markt)
        vpl_allocation.set_ondernemer_filter_kwargs(**self.ondernemer_filter_kwargs)
        vpl_allocation.set_kramen_filter_kwargs(**self.kramen_filter_kwargs)
        vpl_allocation.allocate_own_kramen(Status.EB)
        vpl_allocation.allocate_own_kramen(Status.VPL)
        vpl_allocation.allocate_own_kramen(Status.TVPL)
        vpl_allocation.allocate_own_kramen(Status.EXP)
        vpl_allocation.allocate_own_kramen(Status.EXPF)


class HierarchyStrategy(BaseStrategy):
    def run(self):
        vpl_allocation = VplAllocation(self.markt)
        vpl_allocation.set_ondernemer_filter_kwargs(**self.ondernemer_filter_kwargs)
        vpl_allocation.set_kramen_filter_kwargs(**self.kramen_filter_kwargs)

        self.working_copies.append(self.markt.get_working_copy())
        self.markt.kramen_per_ondernemer = 1

        while self.markt.kramen_per_ondernemer <= self.markt.max_aantal_kramen_per_ondernemer:
            self.trace.set_cycle(self.markt.kramen_per_ondernemer)
            self.markt.restore_working_copy(self.working_copies[0])  # fallback to the initial state
            self.markt.report_indeling()

            vpl_allocation.allocate_tvplz()
            # first expand
            vpl_allocation.vph_uitbreiding(vph_status=Status.EB)
            vpl_allocation.vph_uitbreiding(vph_status=Status.VPL)
            vpl_allocation.vph_uitbreiding(vph_status=Status.TVPL)
            vpl_allocation.vph_uitbreiding(vph_status=Status.EXP)
            vpl_allocation.vph_uitbreiding(vph_status=Status.EXPF)
            # then move to prefs
            vpl_allocation.move_to_prefs(Status.VPL)
            vpl_allocation.move_to_prefs(Status.TVPL)
            vpl_allocation.move_to_prefs(Status.EXP)
            vpl_allocation.move_to_prefs(Status.EXPF)
            # try to move again, because move of others can make move now possible
            vpl_allocation.move_to_prefs(Status.VPL)
            vpl_allocation.move_to_prefs(Status.TVPL)
            vpl_allocation.move_to_prefs(Status.EXP)
            vpl_allocation.move_to_prefs(Status.EXPF)
            # After other vphs have moved, expansion could be possible, so try again
            vpl_allocation.vph_uitbreiding(vph_status=Status.EB)
            vpl_allocation.vph_uitbreiding(vph_status=Status.VPL)
            vpl_allocation.vph_uitbreiding(vph_status=Status.TVPL)
            vpl_allocation.vph_uitbreiding(vph_status=Status.EXP)
            vpl_allocation.vph_uitbreiding(vph_status=Status.EXPF)

            soll_allocation = SollAllocation(self.markt)
            soll_allocation.set_ondernemer_filter_kwargs(**self.ondernemer_filter_kwargs)
            soll_allocation.set_kramen_filter_kwargs(**self.kramen_filter_kwargs)
            soll_allocation.allocate()

            if not self.should_allocation_loop_continue():
                break
        self.finish()

    def finish(self):
        self.trace.debug(f"Finished with kramen_per_ondernemer: {(self.markt.kramen_per_ondernemer - 1) or 1}")
        self.markt.kramen_per_ondernemer = self.markt.max_aantal_kramen_per_ondernemer
        super().finish()


class FillUpStrategyBList(BaseStrategy):
    def run(self):
        self.trace.set_phase(story='allocate_b_list')
        self.working_copies.append(self.markt.get_working_copy())
        self.markt.kramen_per_ondernemer = 1

        while self.markt.kramen_per_ondernemer < self.markt.max_aantal_kramen_per_ondernemer:
            self.trace.set_cycle(self.markt.kramen_per_ondernemer)
            self.markt.restore_working_copy(self.working_copies[0])  # fallback to the initial state

            soll_allocation = SollAllocation(self.markt)
            soll_allocation.set_ondernemer_filter_kwargs(**self.ondernemer_filter_kwargs)
            soll_allocation.set_kramen_filter_kwargs(**self.kramen_filter_kwargs)
            soll_allocation.allocate()
            soll_allocation.allocate_b_list()

            if not self.should_allocation_loop_continue():
                break
        self.finish()

    def finish(self):
        self.trace.debug(f"Finished with kramen_per_ondernemer: {(self.markt.kramen_per_ondernemer - 1) or 1}")
        super().finish()


class OptimizationStrategy(BaseStrategy):
    def __init__(self, markt, **filter_kwargs):
        super().__init__(markt, **filter_kwargs)
        self.fridge = deque()

    def run(self):
        self.trace.set_phase(story='optimize_all')
        self.optimize_all_expansion()
        self.swap_ondernemers()
        self.finish()

    def fill_fridge_with_soll_with_anywhere(self, exclude_ondernemer=None):
        self.trace.set_phase(task='fill_fridge', group=Status.SOLL, agent=PhaseValue.event)
        if not self.fridge:
            self.trace.log(f"Fridge empty, now filling")
            for soll in self.markt.ondernemers.select(status=Status.SOLL, anywhere=True, kraam_type=None):
                if soll == exclude_ondernemer:
                    continue
                if soll.has_verplichte_branche:
                    continue
                kramen_count = len(soll.kramen)
                self.markt.unassign_all_kramen_from_ondernemer(soll)
                self.fridge.append([soll, kramen_count])
                self.trace.log(f"Put soll {soll} with {kramen_count} kramen in fridge")
        self.trace.log(f"Fridge filled ({len(self.fridge)}: {self.fridge}")

    def reassign_ondernemers_from_the_fridge(self):
        self.trace.set_phase(task='reassign_from_fridge', group=Status.SOLL, agent=PhaseValue.event)
        all_allocated = True
        while self.fridge:
            soll, kramen_count = self.fridge.popleft()
            if not kramen_count:
                continue
            cluster = self.markt.kramen.get_cluster(size=kramen_count, ondernemer=soll)
            if cluster:
                cluster.assign(soll)
                if soll.is_rejected:
                    all_allocated = False
            else:
                all_allocated = False
                self.trace.log(f"Could not reassign ondernemer from fridge: {soll}")
        return all_allocated

    def optimize_expansion(self, ondernemer):
        self.trace.set_phase(task='optimize_expansion', group=ondernemer.status, agent=ondernemer.rank)
        current_amount_kramen = len(ondernemer.kramen)
        self.trace.log(f"Optimize expansion {ondernemer}")
        size = min(current_amount_kramen + 1, self.markt.kramen_per_ondernemer)
        branche = ondernemer.branche
        if branche.max:
            available = branche.max - branche.assigned_count
            size = min(size, available + current_amount_kramen)
        cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer,
                                                should_include=ondernemer.kramen,
                                                **self.kramen_filter_kwargs)
        cluster.assign(ondernemer)
        if cluster:
            self.markt.report_indeling()

    def optimize_all_expansion(self):
        working_copies = []
        ondernemers = sorted(self.markt.ondernemers.select(status__in=[*ALL_VPH_STATUS, Status.SOLL], kraam_type=None),
                             key=attrgetter('kramen_count', 'seniority'))
        for ondernemer in ondernemers:
            self.trace.set_phase(task='optimize_expansion', group=ondernemer.status, agent=ondernemer.rank)
            if ondernemer.has_verplichte_branche:
                continue
            if len(ondernemer.kramen) >= ondernemer.max:
                self.trace.log(f"Ondernemer already at max {ondernemer}")
                continue
            working_copies.append(self.markt.get_working_copy())
            self.fill_fridge_with_soll_with_anywhere(exclude_ondernemer=ondernemer)
            self.optimize_expansion(ondernemer)
            all_allocated = self.reassign_ondernemers_from_the_fridge()
            if not all_allocated:
                self.markt.report_indeling()
                self.trace.log(f"Could not optimize expansion for {ondernemer}, fallback to previous markt state")
                self.markt.restore_working_copy(working_copies[-1])
                self.markt.report_indeling()
            else:
                self.markt.report_indeling()

    def swap_ondernemers(self):
        swappers = set()
        ondernemers = self.markt.ondernemers.select(allocated=True)
        for ondernemer in ondernemers:
            for partner in ondernemers:
                if (ondernemer.rank != partner.rank
                        and ondernemer.kramen and len(ondernemer.kramen) == len(partner.kramen)
                        and ondernemer.status == partner.status
                        and set(ondernemer.prefs) == partner.kramen
                        and set(partner.prefs) == ondernemer.kramen):
                    swap = sorted([ondernemer, partner], key=attrgetter('rank'))
                    swap = tuple(swap)
                    swappers.add(swap)
        if swappers:
            self.markt.report_indeling()

        for ondernemer, partner in swappers:
            self.trace.log(f"Swapping kramen from {ondernemer} and {partner}")
            all_kramen = [self.markt.kramen.kramen_map[kraam_id] for kraam_id in [*ondernemer.kramen, *partner.kramen]]
            verplichte_branche_diversity = set([kraam.has_verplichte_branche for kraam in all_kramen])
            kraam_type_diversity = set([kraam.kraam_type.get_active() for kraam in all_kramen])
            if not (len(verplichte_branche_diversity) == 1 and len(kraam_type_diversity) == 1):
                continue

            self.markt.unassign_all_kramen_from_ondernemer(ondernemer)
            self.markt.unassign_all_kramen_from_ondernemer(partner)
            for pref in ondernemer.prefs:
                kraam = self.markt.kramen.kramen_map[pref]
                kraam.assign(ondernemer)
            for pref in partner.prefs:
                kraam = self.markt.kramen.kramen_map[pref]
                kraam.assign(partner)

        if swappers:
            self.markt.report_indeling()
