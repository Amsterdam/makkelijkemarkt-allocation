import redis
import os
from collections import namedtuple

from kjk.logging import clog
from kjk.rejection_reasons import MARKET_FULL


class BranchesScrutenizer:
    """
    The BranchesScrutenizer object will check if the branche positions
    will not exceed the maximum
    """

    def __init__(self, branches):
        self.max_dict = {}
        self.counter_dict = {}
        for b in branches:
            try:
                self.max_dict[b["brancheId"]] = b["maximumPlaatsen"]
                self.counter_dict[b["brancheId"]] = 0
            except KeyError:
                pass  # no max for branche

    def add_allocation(self, branches, stands_to_alloc):
        for branche in branches:
            try:
                self.counter_dict[branche] += len(stands_to_alloc)
            except KeyError:
                pass  # no max for branche

    def allocation_allowed(self, branches):
        allowed = True
        for branche in branches:
            try:
                if self.counter_dict[branche] >= self.max_dict[branche]:
                    allowed = False
            except KeyError:
                pass
        return allowed


class RejectionReasonManager:
    """
    Merchants can be rejected for several reasons.
    If a mechant is not allocation in an allocation-phase,
    a reason will be set for the merchant id.
    If the merchant is still not allocated in later phases, the reason will
    be retreived in the rejection phase.
    """

    def __init__(self):
        self.rejection_reason_dict = {}

    def add_rejection_reason_for_merchant(self, erk, reason):
        self.rejection_reason_dict[erk] = reason

    def get_rejection_reason_for_merchant(self, erk):
        try:
            return self.rejection_reason_dict[erk]
        except KeyError:
            return MARKET_FULL


class PreferredStandFinder:
    """
    To reach an optimal filled market, and allow for maximal expansion:
    1. First we try to find a stand cluster of max wanted stands.
    2. Than we try min wanted stands.
    3. After that we try to find one stand.
    If we come up with a cluster of more than one stand for a 'soll' we can
    not allocate all stands directly. This object get the best position within this
    cluster.
    """

    def __init__(self, cluster, pref):
        self.pref = pref
        self.cluster = cluster

    def produce(self):
        try:
            # try a preferred stand first
            for std in self.pref:
                if std in self.cluster:
                    return [std]
            # no hit, return the first
            return self.cluster[:1]
        except Exception:
            # just in case of failure
            return self.cluster[:1]


class ExpansionOptimizer:
    """
    If multiple merchants have the same expansion options
    try to maximize the number of allocated stands to create a fuller
    market.
    """

    def __init__(self):
        # how many reservations per stand
        self.weighted_expansion_options = {}

    def add_expansion_reservation(self, stands_to_reserve, erk):
        for o in stands_to_reserve:
            if o not in self.weighted_expansion_options:
                self.weighted_expansion_options[o] = 0
            self.weighted_expansion_options[o] += 1
            clog.debug(f"WEIGHTED EXPANSION {self.weighted_expansion_options}")

    def _get_optimized_by_prefs(self, options, erk, prefs, anywhere):
        if len(options) < 2 and anywhere:
            return options
        else:
            for std in prefs:
                for option in options:
                    if std in option:
                        return [option]
            return []

    def get_optimized(self, options, erk, prefs=None, anywhere=True, status=None):
        """
        First check if we have prefs (right now only for EB merchants)
        if an options matches the pref return that option else
        return the option with the lowest weight.
        (fewest expansion claims)
        """
        clog.debug(
            f"GET OPTIMIZED {erk} status: {status} options: {options} prefs: {prefs} anywhere: {anywhere}"
        )
        if prefs is not None:
            # We ignore anywhere (default=True) if EB merchant did not set any prefs
            if len(prefs) == 0 and status == "eb":
                anywhere = True

            result = self._get_optimized_by_prefs(options, erk, prefs, anywhere)
            if len(result) > 0 or not anywhere:
                return result

        if len(options) < 2:
            return options
        else:
            w = 9999
            best_option = None
            for o in options:
                for plaats_id in o:
                    weight = self.weighted_expansion_options.get(plaats_id, 9998)
                    clog.debug(f"GET WEIGHT plaats_id: {plaats_id} weight: {weight}")
                    if weight < w:
                        w = weight
                        best_option = o
            return [best_option]


class MarketStandClusterFinder:

    """
    Find the best combination of market stands in a preference list from the merchant.
    The list is sorted by priority. (most desirable first) We do not want to allocate merchants if stands are not
    adjacent, in another market row or have an obstakel in between.
    """

    MODE_AVOID_PREFS_AND_EXPANSION = 1
    MODE_AVOID_EXPANSION = 2
    MODE_AVOID_PREFS = 3
    MODE_AVOID_NONE = 4

    def __init__(
        self,
        data,
        obstacles,
        branches_dict,
        evi_dict,
        bak_dict,
        branches,
        weighted_prefs=[],
        blocked_stands=[],
    ):
        self.should_check_branche_bak_evi_space = False
        self.weighted_prefs = weighted_prefs
        self.branche_required_dict = {}
        for b in branches:
            try:
                self.branche_required_dict[b["brancheId"]] = b["verplicht"]
            except KeyError:
                self.branche_required_dict[b["brancheId"]] = False

        self.stands_allocated = []
        self.stands_reserved_for_expansion = []
        self.expansion_optimizer = ExpansionOptimizer()
        self.branches_dict = branches_dict
        self.evi_dict = evi_dict
        self.bak_dict = bak_dict
        self.obstacle_dict = self._process_obstacle_dict(obstacles)
        self.flattened_list = []
        self.stands_linked_list = {}
        for k in data:
            for gr in k["indelingslijstGroup"]:
                pl = gr["plaatsList"]
                self.flattened_list.append(None)
                for i, stand_nr in enumerate(pl):
                    if stand_nr in blocked_stands:
                        self.flattened_list.append(["blocked"])
                    else:
                        self.flattened_list.append(stand_nr)
                    try:
                        obs = self.obstacle_dict[str(stand_nr)]
                        self.flattened_list.append(obs)
                    except KeyError:
                        pass
                    if i - 1 >= 0:
                        _prev = pl[i - 1]
                    else:
                        _prev = None
                    _mid = pl[i]
                    try:
                        _next = pl[i + 1]
                    except IndexError:
                        _next = None
                    self.stands_linked_list[_mid] = {"prev": _prev, "next": _next}
        self.flattened_list.append(None)

    def set_market_info_delegate(self, delegate):
        self.market_info_delegate = delegate

    def set_check_branche_bak_evi(self, should_check=False):
        self.should_check_branche_bak_evi_space = should_check

    def set_stands_allocated(self, allocated_stands):
        self.stands_allocated += allocated_stands

    def set_stands_available(self, stands):
        self.stands_allocated = list(set(self.stands_allocated) - set(stands))

    def set_stands_reserved(self, stands_to_reserve, erk=None):
        self.stands_reserved_for_expansion += stands_to_reserve
        self.expansion_optimizer.add_expansion_reservation(stands_to_reserve, erk)

    def _process_obstacle_dict(self, obs):
        d = {}
        for ob in obs:
            d[ob["kraamA"]] = ob["obstakel"]
        return d

    def get_branche_for_stand_id(self, stand_id):
        try:
            return self.branches_dict[stand_id]
        except KeyError:
            return None

    def get_neighbours_for_stand_id(self, stand_id):
        """
        Get the neighbouring stand for a stand_id.
        Can be used to validate an allocation of multiple stands.
        """
        try:
            return self.stands_linked_list[stand_id]
        except KeyError:
            return None

    def filter_preferred(self, valid_options, stand_list):
        """
        return the option containing the highest prio stand (lowest list index)
        """
        for std in stand_list:
            for option in valid_options:
                if std in option:
                    return option
        return []

    def branche_is_required(self, branche_id):
        try:
            return self.branche_required_dict[branche_id]
        except KeyError:
            return False

    def stand_has_required_branche(self, branches):
        for br in branches:
            if self.branche_is_required(br):
                return True
        return False

    def stand_has_evi(self, std):
        try:
            return "eigen-materieel" in self.evi_dict[std]
        except TypeError:
            return False

    def stand_has_bak(self, std):
        try:
            return "bak" == self.bak_dict[std]
        except TypeError:
            return False

    def stand_bak_type(self, std):
        try:
            return self.bak_dict[std]
        except TypeError:
            return "geen"

    def option_is_valid_branche(
        self,
        option,
        merchant_branches,
        bak_merchant,
        evi_merchant,
        erk=None,
        bak_type=None,
    ):
        AV = namedtuple(
            "AllocationVars",
            [
                "merchant_has_required_branche",
                "stand_has_branche",
                "stand_has_required_branche",
                "market_has_unused_bak_space",
                "market_has_unused_evi_space",
                "merchant_has_evi",
                "merchant_has_bak",
                "branches_match",
                "stand_has_evi",
                "stand_has_bak",
                "market_has_unused_branche_space",
                "stand_bak_type",
                "merchant_bak_type",
            ],
            defaults=(None,) * 13,
        )

        illegal_combos = [
            AV(
                merchant_has_required_branche=True,
                branches_match=False,
            ),
            AV(
                merchant_has_bak=True,
                stand_has_bak=False,
            ),
            AV(
                merchant_has_evi=True,
                stand_has_evi=False,
            ),
            AV(
                market_has_unused_branche_space=False,
                branches_match=False,
                stand_has_required_branche=True,
            ),
            AV(
                market_has_unused_bak_space=False,
                merchant_has_bak=False,
                stand_has_bak=True,
            ),
            AV(
                market_has_unused_evi_space=False,
                merchant_has_evi=False,
                stand_has_evi=True,
            ),
            AV(
                merchant_bak_type="bak-licht",
                stand_bak_type="geen",
            ),
        ]

        is_required = self.branche_is_required(merchant_branches[0])
        for std in option:
            try:
                branches = self.branches_dict[std]
            except KeyError:
                # stands input data is not always complete
                branches = []
            stand_required_br = self.stand_has_required_branche(branches)
            std_has_evi = self.stand_has_evi(std)
            std_has_bak = self.stand_has_bak(std)
            std_bak_type = self.stand_bak_type(std)

            # print("- "*23)
            # print("ERK: ", erk)
            # print("stand nr: ", std)
            # print("branches: ", branches)
            # print("stand required branche: ", stand_required_br)
            # print("stand evi: ", std_has_evi)
            # print("stand bak: ", std_has_bak)
            # print("merchant bak: ", bak_merchant)
            # print("merchant evi: ", evi_merchant)
            # print("merchant bak type:", bak_type)
            # print("stand bak type:", std_bak_type)

            # branche
            branch_vars = AV(
                merchant_has_required_branche=is_required,
                branches_match=merchant_branches[0] in branches,
            )
            if branch_vars in illegal_combos:
                return False

            # bak
            bak_vars = AV(
                merchant_has_bak=bak_merchant,
                stand_has_bak=std_has_bak,
            )
            if bak_vars in illegal_combos:
                return False

            # bak licht
            bak_licht_vars = AV(
                merchant_bak_type=bak_type,
                stand_bak_type=std_bak_type,
            )
            if bak_licht_vars in illegal_combos:
                return False

            # evi
            evi_vars = AV(
                merchant_has_evi=evi_merchant,
                stand_has_evi=std_has_evi,
            )
            if evi_vars in illegal_combos:
                return False

            if self.should_check_branche_bak_evi_space:
                evi_space = self.market_info_delegate.market_has_unused_evi_space()

                evi_space_vars = AV(
                    market_has_unused_evi_space=evi_space,
                    merchant_has_evi=evi_merchant,
                    stand_has_evi=std_has_evi,
                )
                if evi_space_vars in illegal_combos:
                    return False

                bak_space = self.market_info_delegate.market_has_unused_bak_space()
                bak_space_vars = AV(
                    market_has_unused_bak_space=bak_space,
                    merchant_has_bak=bak_merchant,
                    stand_has_bak=std_has_bak,
                )
                if bak_space_vars in illegal_combos:
                    return False

                branches_moving_vpl = AV(
                    market_has_unused_branche_space=self.market_info_delegate.market_has_unused_branche_space(
                        branches
                    ),
                    stand_has_required_branche=stand_required_br,
                    branches_match=merchant_branches[0] in branches,
                )
                if branches_moving_vpl in illegal_combos:
                    return False
        return True

    def option_is_available(self, option, mode=None):
        if "STW" in option:
            return False
        if mode == self.MODE_AVOID_PREFS_AND_EXPANSION:
            stands_not_available = (
                self.weighted_prefs
                + self.stands_reserved_for_expansion
                + self.stands_allocated
            )
        elif mode == self.MODE_AVOID_EXPANSION:
            stands_not_available = (
                self.stands_reserved_for_expansion + self.stands_allocated
            )
        elif mode == self.MODE_AVOID_PREFS:
            stands_not_available = self.weighted_prefs + self.stands_allocated
        else:
            stands_not_available = self.stands_allocated
        return not any(elem in option for elem in stands_not_available)

    def option_is_available_for_expansion(self, option):
        if "STW" in option:
            return False
        stands_not_available = self.stands_allocated
        return not any(elem in option for elem in stands_not_available)

    def find_valid_expansion(
        self,
        fixed_positions,
        total_size=0,
        merchant_branche=None,
        bak_merchant=False,
        evi_merchant=False,
        ignore_check_available=None,
        erk=None,
        bak_type=None,
        allocate=False,
        prefs=None,
        anywhere=True,
        status=None,
    ):
        """
        check all adjacent clusters of the requested size,
        and check if the fixed positions are contained in the
        slice. This will be a valid expansion cluster
        """

        valid_options = []
        for i, elem in enumerate(self.flattened_list):
            # an option is valid if it contains the fixed positions
            option = self.flattened_list[i : i + total_size]
            valid = all(elem in option for elem in fixed_positions) and all(
                isinstance(x, str) for x in option
            )

            # NOTE: we remove the already assigned positions from the option
            # this prevents this position to be re-evaluated
            # some vpl or eb merchants have fixed stands assigned by 'marktbureau'
            # that are illegal according to the assigment rules, this would prevent
            # expansion that would normally be legal
            option = [x for x in option if x not in fixed_positions]

            if valid:
                branche_valid_for_option = True
                if merchant_branche:
                    branche_valid_for_option = self.option_is_valid_branche(
                        option,
                        merchant_branche,
                        bak_merchant,
                        evi_merchant,
                        erk=erk,
                        bak_type=bak_type,
                    )
                if ignore_check_available:
                    option = list(set(option) - set(ignore_check_available))
                if branche_valid_for_option and self.option_is_available_for_expansion(
                    option
                ):
                    valid_options.append(option)
        if allocate:
            clog.debug(
                f"EXPANSION GET OPTIMIZED {erk} valid_options: {valid_options} weighted_expansion_options {self.expansion_optimizer.weighted_expansion_options}"
            )
            return self.expansion_optimizer.get_optimized(
                valid_options,
                erk,
                prefs=prefs,
                anywhere=anywhere,
                status=status,
            )
        return valid_options

    def find_valid_cluster(
        self,
        prefs,
        size=2,
        merchant_branche=None,
        evi_merchant=False,
        bak_merchant=False,
        anywhere=True,
        check_branche_bak_evi=True,
        erk=None,
        bak_type=None,
    ):
        """
        check all adjacent clusters of the requested size
        """
        if len(prefs) > 0:
            valid_options = []
            for i, _ in enumerate(self.flattened_list):
                # an option is valid if it is present in de prio list
                option = self.flattened_list[i : i + size]
                valid = any(elem in prefs for elem in option) and all(
                    isinstance(x, str) for x in option
                )
                if valid:
                    branche_valid_for_option = True
                    option_is_available = self.option_is_available(
                        option, mode=self.MODE_AVOID_NONE
                    )
                    if not option_is_available:
                        continue
                    if merchant_branche and check_branche_bak_evi:
                        branche_valid_for_option = self.option_is_valid_branche(
                            option,
                            merchant_branche,
                            bak_merchant,
                            evi_merchant,
                            erk=erk,
                            bak_type=bak_type,
                        )
                    if branche_valid_for_option and option_is_available:
                        valid_options.append(option)
            best_option = self.filter_preferred(valid_options, prefs)
            if len(best_option) > 0 or anywhere == False:
                return best_option

        for mode in (
            self.MODE_AVOID_PREFS_AND_EXPANSION,
            self.MODE_AVOID_PREFS,
            self.MODE_AVOID_NONE,
        ):
            option = self.find_valid_cluster_for_mode(
                size,
                merchant_branche=merchant_branche,
                evi_merchant=evi_merchant,
                bak_merchant=bak_merchant,
                erk=erk,
                mode=mode,
                bak_type=bak_type,
            )
            if option:
                return option
        return []

    def find_valid_cluster_for_mode(
        self,
        size=2,
        merchant_branche=None,
        evi_merchant=False,
        bak_merchant=False,
        erk=None,
        mode=1,
        bak_type=None,
    ):
        valid_options = []
        for i, _ in enumerate(self.flattened_list):
            option = self.flattened_list[i : i + size]
            valid = all(isinstance(x, str) and x != "STW" for x in option)
            if valid:
                branche_valid_for_option = True
                option_is_available = self.option_is_available(option, mode=mode)
                if not option_is_available:
                    continue
                if merchant_branche:
                    branche_valid_for_option = self.option_is_valid_branche(
                        option,
                        merchant_branche,
                        bak_merchant,
                        evi_merchant,
                        erk=erk,
                        bak_type=bak_type,
                    )
                if branche_valid_for_option and option_is_available:
                    if mode != self.MODE_AVOID_NONE:
                        return option
                    else:
                        valid_options.append(option)
        best_option = self.filter_preferred(valid_options, self.weighted_prefs)
        if len(best_option) > 0:
            return best_option


class AllocationDebugger:
    def __init__(self, data):
        self.data = data

    def get_allocation_phase_for_stand(self, stand_id):
        for k in self.data.keys():
            allocs = self.data[k]
            try:
                for alloc in allocs:
                    if stand_id in alloc["stands"]:
                        return f"stand: {stand_id} -> {k}"
            except TypeError:
                pass
        return None

    def get_allocation_phase_for_merchant(self, erk):
        for k in self.data.keys():
            allocs = self.data[k]
            try:
                for alloc in allocs:
                    if erk == alloc["erk"]:
                        return f"merchant: {erk} -> {k}"
            except TypeError:
                pass
        return None


class TradePlacesSolver:
    def __init__(self, data):
        self.data = data
        self.to_dict = {}
        self.from_dict = {}

    def get_position_traders(self):
        traders = []
        for erk in self.data.keys():
            from_pos_list = self.data[erk]["fixed"]
            to_pos_list = self.data[erk]["wanted"]
            from_pos_list.sort()
            to_pos_list.sort()
            from_pos = tuple(from_pos_list)
            to_pos = tuple(to_pos_list)
            self.from_dict[from_pos] = erk
            self.to_dict[to_pos] = erk
        for to in self.to_dict.keys():
            try:
                erk_1 = self.to_dict[to]
                erk = self.from_dict[to]
                if (
                    self.data[erk_1]["fixed"] == self.data[erk]["wanted"]
                    and self.data[erk]["fixed"] == self.data[erk_1]["wanted"]
                ):
                    if erk not in traders and erk_1 not in traders:
                        traders += [erk, erk_1]
            except KeyError:
                pass
        return traders


class DebugRedisClient:
    """
    This a debug only object, it will insert the json file into a local redis
    so the allocation result can be displayed in the KjK application as a concept allocation
    this class will use the redis KEY 'RESULT_1' and the result url http://127.0.0.1:8080/job/1/
    """

    def __init__(self):
        self.r = redis.StrictRedis(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
            db=0,
            password=os.getenv("REDIS_PASSWORD"),
            charset="utf-8",
            decode_responses=True,
        )
        self.r.delete("RESULT_1")

    def insert_test_result(self, allocation_json):
        f = open(allocation_json, "r")
        data = f.read()
        self.r.set("RESULT_1", data)
        f.close()
        print("-" * 60)
        print("View the results here:")
        print("http://127.0.0.1:8080/job/1/")
        print("-" * 60)
