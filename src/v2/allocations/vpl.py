from v2.conf import Status, TraceMixin
from v2.allocations.base_allocation import BaseAllocation


class VplAllocation(TraceMixin, BaseAllocation):
    def allocate_own_kramen(self, vph_status):
        self.trace.log(f"\n====> {vph_status.value} allocate own kramen \n")
        self.trace.set_task('allocate_own_kramen')
        self.trace.set_group(vph_status)
        ondernemers = self.markt.ondernemers.select(status=vph_status, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            for kraam_id in ondernemer.own:
                kraam = self.markt.kramen.get_kraam_by_id(kraam_id=kraam_id)
                if not kraam:
                    logger.log(f"Kraam {kraam_id} does not exist or is blocked")
                else:
                    kraam.assign(ondernemer)
        self.markt.report_indeling()

    def allocate_tvplz(self):
        self.trace.log(f"\n====> TVPLZ \n")
        self.trace.set_task('allocate_tvplz')
        self.trace.set_group(Status.TVPLZ)
        """
        TVPLZ: a TVPL with no vaste kraam (Zonder) from Mercato.
        Typically, purposefully non-existent vaste kramen are assigned to them in Mercato.
        Because these are not available, they receive kramen before soll and uitbreiders.
        Prefs are given as much as possible, and they need to have anywhere=True in case prefs are not available
        """
        ondernemers = self.markt.ondernemers.select(status=Status.TVPLZ, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.log(f"\nTrying to allocate TVPLZ {ondernemer}")
            size = min(ondernemer.max, self.markt.kramen_per_ondernemer)
            peer_prefs = self.markt.ondernemers.get_prefs_from_unallocated_peers(peer_status=ondernemer.status,
                                                                                 **self.ondernemer_filter_kwargs)
            cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer, peer_prefs=peer_prefs,
                                                    **self.kramen_filter_kwargs)
            cluster.assign(ondernemer)
        self.markt.report_indeling()

    def move_to_prefs(self, vph_status):
        self.trace.log(f"\n====> Moving {vph_status}")
        self.trace.set_task('move_to_prefs')
        self.trace.set_group(vph_status)
        ondernemers = self.markt.ondernemers.select(status=vph_status, **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            if set(ondernemer.prefs).difference(ondernemer.own):
                self.trace.log(f"\nTrying to move Ondernemer {ondernemer}")
                size = self.get_right_size_for_ondernemer(ondernemer)
                current_size = len(ondernemer.kramen)
                if size < current_size:
                    self.trace.log(f"Size {size} smaller than current {current_size}, skip moving")
                    continue
                new_cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer,
                                                            **self.kramen_filter_kwargs)
                self.move_ondernemer_to_new_cluster(ondernemer, new_cluster)
                self.markt.report_indeling()

    def vph_uitbreiding(self, vph_status):
        self.trace.log(f"\n====> Uitbreiden {vph_status}")
        self.trace.set_task('vph_uitbreiding')
        self.trace.set_group(vph_status)
        ondernemers = self.markt.ondernemers.select(status=vph_status, **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.log(f"\nUitbreiden van {vph_status} ondernemer {ondernemer}")
            size = self.get_right_size_for_ondernemer(ondernemer)
            current_size = len(ondernemer.kramen)
            if size <= current_size:
                self.trace.log(f"Size {size} not larger than current {current_size}, skip expansion")
                continue

            cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer, should_include=ondernemer.own,
                                                    **self.kramen_filter_kwargs)
            cluster.assign(ondernemer)
            self.markt.report_indeling()
