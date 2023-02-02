from v2.conf import Status
from v2.allocations.base_allocation import BaseAllocation


class SollAllocation(BaseAllocation):
    def find_and_assign_kramen_to_ondernemer(self, ondernemer):
        size = self.get_right_size_for_ondernemer(ondernemer)
        self.trace.log(f"size {size} = min(ondernemer.max: {ondernemer.max}, kramen_per_ondernemer: "
                       f"{self.markt.kramen_per_ondernemer})")
        peer_prefs = self.markt.ondernemers.get_prefs_from_unallocated_peers(peer_status=ondernemer.status,
                                                                             **self.ondernemer_filter_kwargs)
        cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer, peer_prefs=peer_prefs,
                                                **self.kramen_filter_kwargs)
        if not cluster and size > 1:
            lowered_size = size - 1
            cluster = self.markt.kramen.get_cluster(size=lowered_size, ondernemer=ondernemer, peer_prefs=peer_prefs,
                                                    **self.kramen_filter_kwargs)
        cluster.assign(ondernemer)
        self.markt.report_indeling()

    def allocate(self):
        self.trace.set_phase(task='allocate_soll', group=Status.SOLL)
        ondernemers = self.markt.ondernemers.select(status=Status.SOLL, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.find_and_assign_kramen_to_ondernemer(ondernemer)

    def allocate_b_list(self):
        self.trace.set_phase(task='allocate_b_list', group=Status.B_LIST)
        ondernemers = self.markt.ondernemers.select(status=Status.B_LIST, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.find_and_assign_kramen_to_ondernemer(ondernemer)
