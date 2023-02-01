from v2.conf import trace
from v2.helpers import clamp


class BaseAllocation:
    def __init__(self, markt, **filter_kwargs):
        self.markt = markt
        self.ondernemer_filter_kwargs = filter_kwargs
        self.kramen_filter_kwargs = filter_kwargs

    def set_ondernemer_filter_kwargs(self, **filter_kwargs):
        self.ondernemer_filter_kwargs = filter_kwargs

    def set_kramen_filter_kwargs(self, **filter_kwargs):
        self.kramen_filter_kwargs = filter_kwargs

    def get_right_size_for_ondernemer(self, ondernemer):
        current_amount_kramen = len(ondernemer.kramen)
        amount_kramen_wanted = ondernemer.max
        right_size = clamp(current_amount_kramen, amount_kramen_wanted, self.markt.kramen_per_ondernemer)
        trace.log(f"get_right_size_for_ondernemer: (current, wanted, limit)"
              f"{current_amount_kramen, amount_kramen_wanted, self.markt.kramen_per_ondernemer} = {right_size}")
        return right_size

    def move_ondernemer_to_new_cluster(self, ondernemer, new_cluster):
        if not new_cluster:
            return
        if new_cluster.kramen_list == ondernemer.kramen:
            trace.log(f"Not moving, new cluster {new_cluster} same as current kramen for {ondernemer}")
            return

        current_size = len(ondernemer.kramen)
        offset = -abs(current_size)
        is_to_exceed_branche_max = new_cluster.does_exceed_branche_max(ondernemer.branche, offset=offset)
        if not is_to_exceed_branche_max:
            self.markt.kramen.unassign_ondernemer(ondernemer)
            new_cluster.assign(ondernemer)
