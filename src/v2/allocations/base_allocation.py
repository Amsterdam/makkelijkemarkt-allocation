from operator import attrgetter

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
        self.trace.log(f"Calculate branche limit for {branche}")
        limit = self.markt.kramen_per_ondernemer
        self.trace.log(f"Hard limit = kramen_per_ondernemer = {limit}")

        queue = {}
        branche_ondernemers = self.markt.ondernemers.select(branche=branche, status__in=[*ALL_VPH_STATUS, Status.SOLL])
        for branche_ondernemer in branche_ondernemers:
            queue[branche_ondernemer] = len(branche_ondernemer.kramen)
        self.trace.log(f"initial queue: {queue}")

        available = branche.max - branche.assigned_count
        self.trace.log(f"Branche {branche} max {branche.max} - assigned {branche.assigned_count}"
                       f" = available {available}")

        if not queue:
            self.trace.log(f"No queue: use all {available} available")
            return available

        previous_available = available + 1
        while available and available != previous_available:
            lowest = min(queue.values())
            self.trace.log(f"lowest: {lowest}")
            previous_available = available
            for branche_ondernemer in sorted(queue, key=attrgetter('rank')):
                self.trace.log(f"checking branche_ondernemer: {branche_ondernemer}")
                if queue[branche_ondernemer] == lowest < branche_ondernemer.max and available:
                    self.trace.log(f"upgrading branche_ondernemer: {branche_ondernemer}")
                    queue[branche_ondernemer] += 1
                    available -= 1

        self.trace.log(f"optimized queue: {queue}")
        return queue[ondernemer]

    def get_right_size_for_ondernemer(self, ondernemer):
        current_amount_kramen = len(ondernemer.kramen)
        amount_kramen_wanted = ondernemer.max
        self.trace.log(f"get_right_size_for_ondernemer {ondernemer}")

        entitled_kramen = self.markt.kramen_per_ondernemer
        if ondernemer.branche.max:
            branche_limit = self.get_limit_for_ondernemer_with_branche_with_max(ondernemer)
            self.trace.log(f"Branche {ondernemer.branche} limit {branche_limit} kramen")
            entitled_kramen = min(self.markt.kramen_per_ondernemer, branche_limit)
            self.trace.log(f"entitled_kramen = lowest of {branche_limit}, {self.markt.kramen_per_ondernemer}"
                           f" = {entitled_kramen}")
        else:
            self.trace.log(f"entitled_kramen = kramen_per_ondernemer = {entitled_kramen}")
        if ondernemer.is_vph:
            right_size = clamp(current_amount_kramen, amount_kramen_wanted, entitled_kramen)
            self.trace.log(f"(current, wanted, entitled) "
                           f"{current_amount_kramen, amount_kramen_wanted, entitled_kramen}"
                           f" = {right_size}")
        else:
            right_size = min(amount_kramen_wanted, entitled_kramen)
            self.trace.log(f"(wanted, entitled) {amount_kramen_wanted, entitled_kramen} = {right_size}")
        return right_size
