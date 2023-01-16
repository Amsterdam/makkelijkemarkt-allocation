from v2.conf import logger, Status
from v2.allocations.base_allocation import BaseAllocation


class SollAllocation(BaseAllocation):
    def find_and_assign_kramen_to_ondernemer(self, ondernemer):
        size = min(ondernemer.max, self.markt.kramen_per_ondernemer)
        logger.log(f"size {size} = min(ondernemer.max: {ondernemer.max}, kramen_per_ondernemer: "
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
        logger.log(f"\n====> Sollicitanten \n")
        ondernemers = self.markt.ondernemers.select(status=Status.SOLL, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.find_and_assign_kramen_to_ondernemer(ondernemer)

    def allocate_b_list(self):
        logger.log(f"\n====> Sollicitanten op B-Lijst \n")
        ondernemers = self.markt.ondernemers.select(status=Status.B_LIST, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.find_and_assign_kramen_to_ondernemer(ondernemer)
