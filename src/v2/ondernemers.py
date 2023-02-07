import itertools

from v2.conf import TraceMixin, RejectionReason, ALL_VPH_STATUS, ALL_SOLL_STATUS
from v2.branche import Branche
from v2.kramen import KraamType


class Ondernemer(TraceMixin):
    def __init__(self, rank, erkenningsnummer='', description='', branche=None, prefs=None, min=0, max=0, anywhere=False,
                 kramen=None, own=None, status=None, bak=False, bak_licht=False, evi=False):
        self.rank = rank
        self.erkenningsnummer = erkenningsnummer or rank
        self.description = description or rank
        self.branche = branche or Branche()
        self.prefs = prefs or []
        self.min = min
        self.max = max
        self.min = min
        self.anywhere = anywhere
        self.kramen = set(kramen if kramen else [])
        self.own = set(own if own else [])
        self.status = status
        self.kraam_type = KraamType(bak, bak_licht, evi)
        self.is_rejected = False
        self.reject_reason = ''
        self.ignored = False

    def __str__(self):
        return f"Ondernemer {self.rank}, {self.status.value}, b={self.branche.shortname}, min={self.min}, max={self.max}, " \
               f"anywhere={self.anywhere}, prefs: {self.prefs}, kramen: {self.kramen}, " \
               f"kraam_type={str(self.kraam_type) or 'geen'}, own: {self.own}"

    def __repr__(self):
        return str(self)

    @property
    def is_vph(self):
        return self.status in ALL_VPH_STATUS

    def assign_kraam(self, kraam):
        self.kramen.add(kraam)
        self.branche.assigned_count += 1

    def unassign_kraam(self, kraam):
        self.branche.assigned_count -= 1
        self.kramen.remove(kraam)

    def ignore(self):
        self.ignored = True

    def reject(self, reason):
        self.trace.log(f"Rejecting: {reason.value} => {self}")
        self.is_rejected = True
        self.reject_reason = reason

    def likes_proposed_kramen(self, proposed_kramen):
        if self.status in ALL_VPH_STATUS:
            return self.likes_proposed_kramen_as_vph(proposed_kramen)
        if self.status in ALL_SOLL_STATUS:
            return self.likes_proposed_kramen_as_soll(proposed_kramen)
        return False

    def likes_proposed_kramen_as_vph(self, proposed_kramen):
        return True

    def likes_proposed_kramen_as_soll(self, proposed_kramen):
        amount_proposed_kramen = len(proposed_kramen)
        if not proposed_kramen:
            if self.anywhere:
                self.reject(RejectionReason.NO_KRAMEN_WITH_ANYWHERE)
            else:
                self.reject(RejectionReason.NO_KRAMEN)
            return False
        if amount_proposed_kramen < self.min:
            self.reject(RejectionReason.LESS_THAN_MIN)
            return False
        return True


class Ondernemers:
    def __init__(self, ondernemers=None):
        self.ondernemers = ondernemers or []

    def __repr__(self):
        return f'{len(self.ondernemers)} ondernemers'

    def sort_by_rank(self, ondernemers):
        return sorted(ondernemers, key=lambda ondernemer: ondernemer.rank)

    def all(self):
        return self.sort_by_rank(self.ondernemers)

    def get_prefs_from_unallocated_peers(self, peer_status, **filter_kwargs):
        ondernemers = self.select(status=peer_status, allocated=False, **filter_kwargs)
        all_prefs = (ondernemer.prefs for ondernemer in ondernemers)
        return set(itertools.chain.from_iterable(all_prefs))

    def select(self, **filter_kwargs):
        filters = []
        selected = []
        prop_names = ['status', 'branche', 'kraam_type']
        bool_prop_names = ['anywhere', 'is_soft_rejected', 'ignored']
        for kwarg in filter_kwargs:
            if kwarg in [*prop_names, *bool_prop_names]:
                filters.append(lambda ondernemer, kwarg=kwarg: getattr(ondernemer, kwarg) == filter_kwargs[kwarg])
            elif kwarg == 'allocated':
                filters.append(lambda ondernemer: bool(ondernemer.kramen) is filter_kwargs['allocated'])

            for prop_name in prop_names:
                in_prop_name = f"{prop_name}__in"
                not_in_prop_name = f"{prop_name}__not__in"
                if kwarg == in_prop_name:
                    filters.append(lambda ondernemer, prop_name=prop_name, in_prop_name=in_prop_name:
                                   getattr(ondernemer, prop_name) in filter_kwargs[in_prop_name])
                elif kwarg == not_in_prop_name:
                    filters.append(lambda ondernemer, prop_name=prop_name, not_in_prop_name=not_in_prop_name:
                                   getattr(ondernemer, prop_name) not in filter_kwargs[not_in_prop_name])

        for ondernemer in self.ondernemers:
            results = [f(ondernemer) for f in filters]
            if all(results):
                selected.append(ondernemer)
        return self.sort_by_rank(selected)
