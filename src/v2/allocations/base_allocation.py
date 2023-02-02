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
        branche = ondernemer.branche
        limit = self.markt.kramen_per_ondernemer
        branche_ondernemers = self.markt.ondernemers.select(branche=branche)
        eligible_ondernemers = []
        for branche_ondernemer in branche_ondernemers:
            if branche_ondernemer.status == Status.SOLL:
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

        if ondernemers_count * limit <= available:
            self.trace.log(f"Everyone can get {limit} extra")
            return limit
        if limit + ondernemers_count_minus_one * (limit - 1) <= available:
            self.trace.log(f"This one can get {limit} extra, the others one less: {limit - 1}")
            return limit
        if ondernemers_count * (limit - 1) <= available:
            self.trace.log(f"Everyone can get one less extra: {limit - 1}")
            return limit - 1
        else:
            self.trace.log(f"Everyone can just get one")
            return 1

    def get_right_size_for_ondernemer(self, ondernemer):
        current_amount_kramen = len(ondernemer.kramen)
        amount_kramen_wanted = ondernemer.max
        limit = self.markt.kramen_per_ondernemer
        self.trace.log(f"get_right_size_for_ondernemer {ondernemer.status}")
        if ondernemer.branche.max:
            branche_limit = self.get_limit_for_ondernemer_with_branche_with_max(ondernemer) + current_amount_kramen
            limit = min(limit, branche_limit)
            self.trace.log(f"Branche {ondernemer.branche} hard limit to {limit}")

        if ondernemer.is_vph:
            entitled = self.markt.kramen_per_ondernemer + current_amount_kramen
            limit = min(entitled, limit)
            right_size = clamp(current_amount_kramen, amount_kramen_wanted, limit)
            self.trace.log(f"(current, wanted, limit) "
                           f"{current_amount_kramen, amount_kramen_wanted, limit}"
                           f" = {right_size}")
        else:
            right_size = min(amount_kramen_wanted, limit)
            self.trace.log(f"(wanted, limit) {amount_kramen_wanted, limit} = {right_size}")
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
