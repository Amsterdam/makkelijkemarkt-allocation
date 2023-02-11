from collections import defaultdict

from v2.conf import KraamTypes, RejectionReason, TraceMixin


class KraamType:
    def __init__(self, bak=False, bak_licht=False, evi=False):
        self.props = []
        # order should be: evi, bak_licht, bak
        if evi:
            self.props.append(KraamTypes.EVI)
        if bak_licht:
            self.props.append(KraamTypes.BAK_LICHT)
        if bak:
            self.props.append(KraamTypes.BAK)

    def __str__(self):
        return ''.join(prop.value for prop in self.props)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return other in self.props

    def __bool__(self):
        return bool(self.props)

    def as_dict(self):
        return {
            'B': KraamTypes.BAK in self.props,
            'L': KraamTypes.BAK_LICHT in self.props,
            'E': KraamTypes.EVI in self.props,
        }

    def get_active(self):
        try:
            return self.props[-1]
        except (KeyError, IndexError):
            pass

    def remove_active(self):
        try:
            return self.props.pop()
        except KeyError:
            pass

    def does_allow(self, kraam_type):
        active_prop = self.get_active()
        if not active_prop:
            return True
        if not kraam_type:
            return False
        if active_prop == KraamTypes.BAK:
            return kraam_type in [KraamTypes.BAK, KraamTypes.BAK_LICHT]
        else:
            return kraam_type == active_prop


class Kraam(TraceMixin):
    def __init__(self, id, ondernemer=None, branche=None, **kwargs):
        self.id = id
        self.ondernemer = ondernemer
        self.branche = branche
        self.kraam_type = KraamType(**kwargs)

    def __str__(self):
        kraam = f"kraam {self.id}"
        branche = self.get_verplichte_branche()
        kraam_type = self.kraam_type.get_active()

        if branche or kraam_type:
            kraam += f" ({branche}{kraam_type.value if kraam_type else ''})"
        return kraam

    def get_verplichte_branche(self):
        return self.branche.shortname if (self.branche and self.branche.verplicht) else ''

    def __repr__(self):
        return str(self)

    def does_allow_ondernemer_branche(self, ondernemer):
        if not (self.branche and self.branche.verplicht):
            return True
        if self.branche == ondernemer.branche:
            return True
        else:
            self.trace.log(f"Kraam {self} not allowed, different verplichte branche than ondernemer {ondernemer}")
            return False

    def does_allow_ondernemer_kraam_type(self, ondernemer):
        if self.kraam_type.does_allow(ondernemer.kraam_type):
            return True
        else:
            self.trace.log(f"Kraam {self} not allowed, different verplichte kraam_type than ondernemer {ondernemer}")
            return False

    def does_allow(self, ondernemer):
        return self.does_allow_ondernemer_branche(ondernemer) and self.does_allow_ondernemer_kraam_type(ondernemer)

    def assign(self, ondernemer):
        if self.ondernemer:
            if self.ondernemer == ondernemer.rank:
                self.trace.log(f"Kraam {self.id} already assigned to own")
            else:
                self.trace.log(f"WARNING: kraam {self.id} already assigned to ondernemer {ondernemer}")
        else:
            self.trace.log(f"Assigning kraam {self.id} to ondernemer {ondernemer}")
            self.ondernemer = ondernemer.rank
            self.trace.assign_kraam_to_ondernemer(self.id, ondernemer.rank)
            ondernemer.assign_kraam(self.id)

    def unassign(self, ondernemer):
        if self.ondernemer == ondernemer.rank:
            self.trace.log(f"Unassigning kraam {self.id} from ondernemer {ondernemer}")
            self.ondernemer = None
            self.trace.unassign_kraam(self.id)
            ondernemer.unassign_kraam(self.id)
        else:
            self.trace.log("Could not unassign {self.id}, not owned by {ondernemer.rank} but {self.ondernemer}")

    def remove_verplichte_branche(self, branche):
        if self.branche == branche and self.branche.verplicht:
            self.branche = None
            self.trace.log(f"Removed verplichte branche {branche} from {self}")
        else:
            self.trace.log(f"WARNING: kraam {self} does not have verplichte branche {branche}")


class Cluster(TraceMixin):
    def __init__(self, kramen=None):
        self.kramen = kramen or []
        self.kramen_list = {kraam.id for kraam in self.kramen}

    def __str__(self):
        return f"[{','.join(str(kraam) for kraam in self.kramen)}]"

    def __repr__(self):
        return str(self)

    def __bool__(self):
        return bool(self.kramen)

    def has_props(self, **filter_kwargs):
        if not filter_kwargs:
            return True
        # logger.log(f"Checking for props: {filter_kwargs}")
        check_props = []
        for kwarg in filter_kwargs:
            if kwarg in ['branche', 'verplicht', 'id', 'kraam_type']:
                check_props.append(lambda kraam, kwarg=kwarg: getattr(kraam, kwarg) == filter_kwargs[kwarg])

        for kraam in self.kramen:
            results = [check_prop(kraam) for check_prop in check_props]
            if not all(results):
                return False
        return True

    def matches_ondernemer_prefs(self, ondernemer):
        for kraam in self.kramen:
            if kraam.id not in ondernemer.prefs:
                return False
        return True

    def is_available(self, ondernemer=None):
        available_status = [None]
        if ondernemer:
            available_status.append(ondernemer.rank)
        return all(kraam.ondernemer in available_status for kraam in self.kramen)

    def is_allowed(self, ondernemer):
        return all(kraam.does_allow(ondernemer) for kraam in self.kramen)

    def does_exceed_branche_max(self, ondernemer):
        branche = ondernemer.branche
        if branche.max:
            current_size = len(ondernemer.kramen)
            offset = -abs(current_size)
            if branche.assigned_count + len(self.kramen) + offset > branche.max:
                self.trace.log(f"WARNING: Amount of kramen {len(self.kramen) - offset} plus {branche.assigned_count} "
                               f"exceeds branche '{branche}' max of {branche.max}")
                return True
        return False

    def validate_assignment(self, ondernemer):
        if self.does_exceed_branche_max(ondernemer):
            ondernemer.reject(RejectionReason.EXCEEDS_BRANCHE_MAX)
            return False
        if not ondernemer.likes_proposed_kramen(self.kramen):
            return False
        return True

    def assign(self, ondernemer):
        is_valid = self.validate_assignment(ondernemer)
        if is_valid:
            for kraam in self.kramen:
                kraam.assign(ondernemer)

    def unassign(self, ondernemer):
        for kraam in self.kramen:
            kraam.unassign(ondernemer)

    def remove_verplichte_branche(self, *args, **kwargs):
        for kraam in self.kramen:
            kraam.remove_verplichte_branche(*args, **kwargs)

    def calculate_cluster_matching_prefs_score(self, prefs):
        max_possible_score = len(prefs)
        cluster_score = 0
        for kraam in self.kramen:
            try:
                index = prefs.index(kraam.id)
                if index >= 0:
                    kraam_score = (max_possible_score - index) ** 2
                    cluster_score += kraam_score
            except ValueError:
                pass
        return cluster_score


class Kramen(TraceMixin):
    def __init__(self, rows):
        self.rows = rows
        self.kramen_map = {}
        for row in rows:
            for kraam in row:
                self.kramen_map[kraam.id] = kraam

    def get_kraam_by_id(self, kraam_id):
        return self.kramen_map.get(kraam_id)

    def as_rows(self):
        return self.rows

    def as_flat_rows(self):
        return [
            [{
                'id': kraam.id,
                'branche': kraam.get_verplichte_branche(),
                'kraamType': kraam.kraam_type.as_dict(),
            } for kraam in row] for row in self.rows]

    def calculate_allocation_hash(self):
        allocation = []
        for kraam in self.kramen_map.values():
            allocation.append((kraam.id, kraam.ondernemer))
        frozen = frozenset(allocation)
        return hash(frozen)

    def unassign_ondernemer(self, ondernemer):
        for kraam in self.kramen_map.values():
            if kraam.ondernemer == ondernemer.rank:
                kraam.unassign(ondernemer)

    def remove_verplichte_branche(self, branche):
        for kraam in self.kramen_map.values():
            if kraam.branche and kraam.branche.verplicht and kraam.branche == branche:
                kraam.remove_verplichte_branche(branche)

    def remove_kraam_type(self, kraam_type):
        for kraam in self.kramen_map.values():
            if kraam.branche and kraam.branche.verplicht:
                continue
            if kraam.kraam_type == kraam_type:
                active_prop = kraam.kraam_type.remove_active()
                self.trace.log(f"Removed active prop {active_prop} from kraam {kraam}")

    def order_clusters_by_ondernemer_prefs(self, clusters, ondernemer):
        prefs = ondernemer.prefs
        if not prefs:
            return []

        pref_clusters = defaultdict(list)
        ordered_pref_clusters = []

        for cluster in clusters:
            cluster_score = cluster.calculate_cluster_matching_prefs_score(prefs)
            if cluster_score:
                self.trace.log(f"Scoring: cluster: {cluster}, prefs: {prefs}, cluster_score: {cluster_score}")
                pref_clusters[cluster_score].append(cluster)

        for key in sorted(pref_clusters.keys(), reverse=True):
            ordered_pref_clusters.extend(pref_clusters[key])
        return ordered_pref_clusters

    def exclude_clusters_preferred_by_peers(self, clusters, peer_prefs):
        for cluster in clusters:
            if cluster.kramen_list.intersection(peer_prefs):
                # logger.log(f"Cluster {cluster} in peer prefs: {peer_prefs}")
                pass
            else:
                yield cluster

    def make_clusters(self, size=1):
        clusters = []
        for row in self.rows:
            for index in range(len(row)):
                cluster = row[index:index + size]
                if len(cluster) == size:
                    clusters.append(Cluster(cluster))
        return clusters

    def find_clusters(self, size=1, ondernemer=None, **filter_kwargs):
        clusters = []
        for cluster in self.make_clusters(size):
            if cluster.is_available(ondernemer) and cluster.has_props(**filter_kwargs):
                clusters.append(cluster)
        if ondernemer:
            self.trace.log(f"Found {len(clusters)} clusters of {size} for ondernemer {ondernemer}: {clusters}")
        return clusters

    def get_cluster(self, size, ondernemer, peer_prefs=None, should_include=None, **filter_kwargs):
        anywhere = getattr(ondernemer, 'anywhere', False)
        peer_prefs = peer_prefs or []

        clusters = self.find_clusters(size, ondernemer, **filter_kwargs)
        clusters = [cluster for cluster in clusters if cluster.is_allowed(ondernemer)]
        if should_include:
            should_include = set(should_include)
            clusters = [cluster for cluster in clusters if should_include.issubset(cluster.kramen_list)]
            self.trace.log(f"Should include {should_include}: {clusters}")
        pref_clusters = self.order_clusters_by_ondernemer_prefs(clusters, ondernemer)

        self.trace.log(f"Anywhere {anywhere}")
        if anywhere or should_include:
            pref_clusters.extend(self.exclude_clusters_preferred_by_peers(clusters, peer_prefs))
            pref_clusters.extend(clusters)
        self.trace.log(f"Best matching clusters: {pref_clusters}")
        first = next(iter(pref_clusters), Cluster())
        return first
