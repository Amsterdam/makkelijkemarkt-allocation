from v2.conf import TraceMixin, Status

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

    def is_allocation_valid(self):
        return self.markt.is_allocation_valid(**self.ondernemer_filter_kwargs)

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

        if not self.kramen_still_available():
            return False

        if not self.is_allocation_valid():
            if self.markt.kramen_per_ondernemer > 1:
                self.markt.restore_working_copy(self.working_copies[-1])  # fallback to the previous state
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
        super().finish()


class FillUpStrategyBList(BaseStrategy):
    def run(self):
        self.working_copies.append(self.markt.get_working_copy())
        self.markt.kramen_per_ondernemer = 1

        while self.markt.kramen_per_ondernemer < self.markt.max_aantal_kramen_per_ondernemer:
            self.markt.restore_working_copy(self.working_copies[0])  # fallback to the initial state

            soll_allocation = SollAllocation(self.markt)
            soll_allocation.set_ondernemer_filter_kwargs(**self.ondernemer_filter_kwargs)
            soll_allocation.set_kramen_filter_kwargs(**self.kramen_filter_kwargs)
            soll_allocation.allocate_b_list()

            if not self.should_allocation_loop_continue():
                break
        self.finish()

    def finish(self):
        self.trace.debug(f"Finished with kramen_per_ondernemer: {(self.markt.kramen_per_ondernemer - 1) or 1}")
        super().finish()


class OptimizationStrategy(BaseStrategy):
    def run(self):
        vpl_allocation = VplAllocation(self.markt)
        vpl_allocation.maximize_vph()
        self.finish()
