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
                if not kraam:
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
            size = min(ondernemer.max, self.markt.kramen_per_ondernemer)
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
                if size < current_size:
                    self.trace.log(f"Size {size} smaller than current {current_size}, skip moving")
                    continue
                new_cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer,
                                                            **self.kramen_filter_kwargs)
                self.markt.kramen.move_ondernemer_to_new_cluster(ondernemer, new_cluster)
                self.markt.report_indeling()

    def maximize_vph(self):
        ondernemers = self.markt.ondernemers.select(status__in=ALL_VPH_STATUS, **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.set_phase(task='maximize_vph', group=ondernemer.status)
            current_amount_kramen = len(ondernemer.kramen)
            if current_amount_kramen < ondernemer.max:
                self.trace.log(f"VPH maximize expansion {ondernemer}")
                size = ondernemer.max
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

    def vph_uitbreiding(self, vph_status):
        self.trace.set_phase(task='vph_uitbreiding', group=vph_status)
        ondernemers = self.markt.ondernemers.select(status=vph_status, **self.ondernemer_filter_kwargs)
        for ondernemer in ondernemers:
            self.trace.set_phase(agent=ondernemer.rank)
            self.trace.log(f"Uitbreiden van {vph_status} ondernemer {ondernemer}")
            size = self.get_right_size_for_ondernemer(ondernemer)
            current_size = len(ondernemer.kramen)

            if size < current_size:
                self.trace.log(f"Current kramen size {size} smaller than current {current_size}, skip expansion")
                continue
            if size == current_size:
                self.trace.log(f"Size {size} same as {current_size}")
                if not ondernemer.prefs:
                    self.trace.log(f"No prefs, skip expansion")
                    continue
                elif ondernemer.prefs and set(ondernemer.prefs).intersection(ondernemer.kramen):
                    self.trace.log(f"Current kramen matching with prefs, skip expansion")
                    continue
                else:
                    self.trace.log(f"Current kramen {ondernemer.kramen} not matching with prefs {ondernemer.prefs}")
            cluster = self.markt.kramen.get_cluster(size=size, ondernemer=ondernemer,
                                                    should_include=ondernemer.kramen, **self.kramen_filter_kwargs)
            if ondernemer.status == Status.EB:
                contains_own_kramen = set(ondernemer.own).intersection(cluster.kramen_list)
                contains_prefs = set(ondernemer.prefs).intersection(cluster.kramen_list)
                if not contains_own_kramen or not contains_prefs:
                    return

            cluster.assign(ondernemer)
            if cluster:
                self.markt.report_indeling()
