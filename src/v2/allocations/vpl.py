from v2.conf import Status, RejectionReason, Status,  ALL_VPH_STATUS
from v2.allocations.base_allocation import BaseAllocation


class VplAllocation(BaseAllocation):
    def allocate_own_kramen(self, vph_status):
        self.trace.set_phase(task='allocate_own_kramen', group=vph_status)
        ondernemers = self.markt.ondernemers.select(status=vph_status, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.set_phase(agent=ondernemer.rank)
            for kraam_id in ondernemer.own:
                kraam = self.markt.kramen.get_kraam_by_id(kraam_id=kraam_id)
                if not kraam or kraam.is_blocked:
                    self.trace.log(f"Kraam {kraam_id} does not exist or is blocked")
                    ondernemer.reject(RejectionReason.KRAAM_DOES_NOT_EXIST)
                else:
                    kraam.assign(ondernemer)
        if ondernemers:
            self.markt.report_indeling()

    def allocate_tvplz(self):
        self.trace.set_phase(task='allocate_tvplz', group=Status.TVPLZ)
        """
        TVPLZ: a TVPL with no vaste kraam (Zonder) from Mercato.
        Typically, purposefully non-existent vaste kramen are assigned to them in Mercato.
        Because these are not available, they receive kramen before soll and uitbreiders.
        Prefs are given as much as possible, and they need to have anywhere=True in case prefs are not available
        """
        ondernemers = self.markt.ondernemers.select(status=Status.TVPLZ, allocated=False,
                                                    **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.set_phase(agent=ondernemer.rank)
            self.trace.log(f"Trying to allocate TVPLZ {ondernemer}")
            size = len(ondernemer.own)
            peer_prefs = self.markt.ondernemers.get_prefs_from_unallocated_peers(peer_status=ondernemer.status,
                                                                                 **self.ondernemer_filter_kwargs)
            cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer, peer_prefs=peer_prefs,
                                                    **self.kramen_filter_kwargs)
            cluster.assign(ondernemer)
        if ondernemers:
            self.markt.report_indeling()

    def move_to_prefs(self, vph_status):
        self.trace.set_phase(task='move_to_prefs', group=vph_status)
        ondernemers = self.markt.ondernemers.select(status=vph_status, **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.set_phase(agent=ondernemer.rank)
            if set(ondernemer.prefs).difference(ondernemer.own):
                self.trace.log(f"Trying to move Ondernemer {ondernemer}")
                size = self.get_right_size_for_ondernemer(ondernemer)
                current_size = len(ondernemer.kramen)

                new_cluster = None
                while not new_cluster and size >= current_size:
                    new_cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer,
                                                                **self.kramen_filter_kwargs)
                    size -= 1

                self.markt.kramen.move_ondernemer_to_new_cluster(ondernemer, new_cluster)
                self.markt.report_indeling()

    def vph_uitbreiding(self, vph_status):
        self.trace.set_phase(task='vph_uitbreiding', group=vph_status)
        ondernemers = self.markt.ondernemers.select(status=vph_status, **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.expand_vph(ondernemer)

    def expand_vph(self, ondernemer):
        self.trace.set_phase(agent=ondernemer.rank)
        self.trace.log(f"Uitbreiden van ondernemer {ondernemer}")
        size = self.get_right_size_for_ondernemer(ondernemer)
        current_size = len(ondernemer.kramen)

        if size < current_size:
            self.trace.log(f"Current kramen size {size} smaller than current {current_size}, skip expansion")
            return
        if size == current_size:
            self.trace.log(f"Size {size} same as {current_size}")
            if not ondernemer.prefs:
                self.trace.log(f"No prefs, skip expansion")
                return
            elif ondernemer.prefs and set(ondernemer.prefs).intersection(ondernemer.kramen):
                self.trace.log(f"Current kramen matching with prefs, skip expansion")
                return
            else:
                self.trace.log(f"Current kramen {ondernemer.kramen} not matching with prefs {ondernemer.prefs}")
        cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer,
                                                should_include=ondernemer.kramen, **self.kramen_filter_kwargs)
        cluster.assign(ondernemer)
        if cluster:
            self.markt.report_indeling()
