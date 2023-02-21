from v2.conf import Status
from v2.allocations.base_allocation import BaseAllocation
from v2.kramen import Cluster


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
            size -= 1
            cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer, peer_prefs=peer_prefs,
                                                    **self.kramen_filter_kwargs)
        if not cluster and not ondernemer.anywhere:
            cluster = self.keep_on_lowering_size_to_find_cluster(size, ondernemer, peer_prefs)
        cluster.assign(ondernemer)
        self.markt.report_indeling()

    def allocate(self):
        self.trace.set_phase(task='allocate_soll', group=Status.SOLL)
        ondernemers = self.markt.ondernemers.select(status=Status.SOLL, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.set_phase(agent=ondernemer.rank)
            self.find_and_assign_kramen_to_ondernemer(ondernemer)

    def allocate_b_list(self):
        self.trace.set_phase(task='allocate_b_list', group=Status.B_LIST)
        ondernemers = self.markt.ondernemers.select(status=Status.B_LIST, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.set_phase(agent=ondernemer.rank)
            self.find_and_assign_kramen_to_ondernemer(ondernemer)

    def keep_on_lowering_size_to_find_cluster(self, size, ondernemer, peer_prefs):
        cluster = Cluster()
        while size >= 1:
            self.trace.log(f"Trying to find cluster with size {size} because anywhere is False for "
                           f"ondernemer {ondernemer}")
            cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer, peer_prefs=peer_prefs,
                                                    **self.kramen_filter_kwargs)
            if cluster:
                break
            else:
                size -= 1
        return cluster
