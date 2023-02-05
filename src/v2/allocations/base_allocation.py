from v2.conf import TraceMixin, ALL_VPH_STATUS, Status
from v2.helpers import clamp


class BaseAllocation(TraceMixin):
    def __init__(self, markt, **filter_kwargs):
        self.markt = markt
        self.ondernemer_filter_kwargs = filter_kwargs
        self.kramen_filter_kwargs = filter_kwargs

    def set_ondernemer_filter_kwargs(self, **filter_kwargs):
        self.ondernemer_filter_kwargs = filter_kwargs

    def set_kramen_filter_kwargs(self, **filter_kwargs):
        self.kramen_filter_kwargs = filter_kwargs

    def get_limit_for_ondernemer_with_branche_with_max(self, ondernemer):
        """
        Returns how many extra kramen the ondernemer is allowed to claim
        """
        branche = ondernemer.branche

        if ondernemer.is_vph:
            branche_ondernemers = self.markt.ondernemers.select(branche=branche, status__in=ALL_VPH_STATUS)
            branche_ondernemers = [o for o in branche_ondernemers if o.rank >= ondernemer.rank]
            branche_ondernemers = [*branche_ondernemers,
                                   *self.markt.ondernemers.select(branche=branche, status=Status.SOLL)]
        else:
            branche_ondernemers = self.markt.ondernemers.select(branche=branche, status=Status.SOLL)
            branche_ondernemers = [o for o in branche_ondernemers if o.rank >= ondernemer.rank]

        eligible_ondernemers = []
        for branche_ondernemer in branche_ondernemers:
            if branche_ondernemer.status == Status.SOLL and not branche_ondernemer.kramen:
                eligible_ondernemers.append(branche_ondernemer)
            if branche_ondernemer.status in ALL_VPH_STATUS:
                if len(branche_ondernemer.kramen) < branche_ondernemer.max:
                    eligible_ondernemers.append(branche_ondernemer)

        ondernemers_count = len(eligible_ondernemers)
        ondernemers_count_minus_one = max(ondernemers_count - 1, 0)
        available = branche.max - branche.assigned_count
        self.trace.log(f"Branche {branche} max {branche.max} - assigned {branche.assigned_count}"
                       f" = available {available}")
        self.trace.log(f"With {ondernemers_count} ondernemers interested")

        limit = 0
        while limit <= self.markt.max_aantal_kramen_per_ondernemer:
            if ondernemers_count * limit <= available:
                limit += 1
                continue
            if limit + ondernemers_count_minus_one * (limit - 1) <= available:
                limit += 1
                continue
            else:
                break
        return max(limit - 1, 0)

    def get_right_size_for_ondernemer(self, ondernemer):
        current_amount_kramen = len(ondernemer.kramen)
        amount_kramen_wanted = ondernemer.max
        self.trace.log(f"get_right_size_for_ondernemer {ondernemer}")

        entitled_extra_kramen = self.markt.kramen_per_ondernemer
        if ondernemer.branche.max:
            branche_limit = self.get_limit_for_ondernemer_with_branche_with_max(ondernemer)
            self.trace.log(f"Branche {ondernemer.branche} limit {branche_limit} extra kramen")
            entitled_extra_kramen = min(self.markt.kramen_per_ondernemer, branche_limit)
            self.trace.log(f"entitled_extra_kramen = lowest of {branche_limit}, {self.markt.kramen_per_ondernemer}"
                           f" = {entitled_extra_kramen}")

        if ondernemer.is_vph:
            entitled_kramen = current_amount_kramen + entitled_extra_kramen
            self.trace.log(f"entitled_kramen = current {current_amount_kramen}"
                           f" + entitled extra {entitled_extra_kramen} = {entitled_kramen}")
            right_size = clamp(current_amount_kramen, amount_kramen_wanted, entitled_kramen)
            self.trace.log(f"(current, wanted, entitled) "
                           f"{current_amount_kramen, amount_kramen_wanted, entitled_kramen}"
                           f" = {right_size}")
        else:
            entitled_kramen = entitled_extra_kramen
            self.trace.log(f"entitled_kramen = {entitled_kramen}")
            right_size = min(amount_kramen_wanted, entitled_kramen)
            self.trace.log(f"(wanted, entitled) {amount_kramen_wanted, entitled_kramen} = {right_size}")
        return right_size

    def move_ondernemer_to_new_cluster(self, ondernemer, new_cluster):
        if not new_cluster:
            return
        if new_cluster.kramen_list == ondernemer.kramen:
            self.trace.log(f"Not moving, new cluster {new_cluster} same as current kramen for {ondernemer}")
            return

        current_size = len(ondernemer.kramen)
        offset = -abs(current_size)
        is_to_exceed_branche_max = new_cluster.does_exceed_branche_max(ondernemer.branche, offset=offset)
        if not is_to_exceed_branche_max:
            self.markt.kramen.unassign_ondernemer(ondernemer)
            new_cluster.assign(ondernemer)
