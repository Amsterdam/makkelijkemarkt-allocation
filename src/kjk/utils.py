import redis
import sys
import os
from collections import namedtuple
import traceback


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

    def add_allocation(self, branches):
        for branche in branches:
            try:
                self.counter_dict[branche] += 1
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


class MarketStandClusterFinder:

    """
    Find the best combination of market stands in a preference list from the merchant.
    The list is sorted by priority. (most desirable first) We do not want to allocate merchants if stands are not
    adjacent, in another market row or have an obstakel in between.
    """

    def __init__(self, data, obstacles, branches_dict, evi_dict, branches):
        self.prevent_evi = False
        self.branche_required_dict = {}
        for b in branches:
            try:
                self.branche_required_dict[b["brancheId"]] = b["verplicht"]
            except KeyError:
                self.branche_required_dict[b["brancheId"]] = False

        self.stands_allocated = []
        self.stands_reserved_for_expansion = []
        self.branches_dict = branches_dict
        self.evi_dict = evi_dict
        self.obstacle_dict = self._process_obstacle_dict(obstacles)
        self.flattened_list = []
        self.stands_linked_list = {}
        for k in data:
            for gr in k["indelingslijstGroup"]:
                pl = gr["plaatsList"]
                self.flattened_list.append(None)
                for i, stand_nr in enumerate(pl):
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

    def set_prevent_evi(self, prevent_evi):
        self.prevent_evi = prevent_evi

    def set_stands_allocated(self, allocated_stands):
        self.stands_allocated += allocated_stands

    def set_stands_reserved(self, stands_to_reserve):
        self.stands_reserved_for_expansion += stands_to_reserve

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
            return []

    def option_is_valid_branche(
        self, option, merchant_branches, evi_merchant, prevent_evi=False
    ):
        AV = namedtuple(
            "AllocationVars",
            [
                "merchant_has_required_branche",
                "stand_has_branche",
                "stand_has_required_branche",
                "market_has_unused_evi_space",
                "merchant_has_evi",
                "branches_match",
                "stand_has_evi",
                "prevent_evi",
            ],
            defaults=(None,) * 8,
        )

        illegal_combos = [
            AV(
                merchant_has_required_branche=True,
                branches_match=False,
            ),
            AV(
                merchant_has_evi=True,
                stand_has_evi=False,
            ),
            AV(
                market_has_unused_evi_space=False,
                merchant_has_evi=False,
                stand_has_evi=True,
                stand_has_branche=True,
                stand_has_required_branche=True,
                branches_match=False,
            ),
            AV(
                market_has_unused_evi_space=False,
                stand_has_branche=True,
                stand_has_required_branche=True,
                merchant_has_required_branche=False,
                merchant_has_evi=False,
            ),
            AV(market_has_unused_evi_space=False, prevent_evi=True, stand_has_evi=True),
        ]

        is_required = self.branche_is_required(merchant_branches[0])
        try:
            for std in option:
                branches = self.branches_dict[std]

                # do the branches match?
                branch_vars = AV(
                    merchant_has_required_branche=is_required,
                    branches_match=merchant_branches[0] in branches,
                )
                if branch_vars in illegal_combos:
                    return False

                # do evi spec match?
                evi_vars = AV(
                    merchant_has_evi=evi_merchant,
                    stand_has_evi=self.stand_has_evi(std),
                )
                if evi_vars in illegal_combos:
                    return False

                # do evi spec match?
                evi_space_vars = AV(
                    market_has_unused_evi_space=self.market_info_delegate.market_has_unused_evi_space(),
                    merchant_has_evi=evi_merchant,
                    stand_has_evi=self.stand_has_evi(std),
                )
                if evi_space_vars in illegal_combos:
                    return False

                # do evi spec match?
                evi_space_vars = AV(
                    market_has_unused_evi_space=self.market_info_delegate.market_has_unused_evi_space(),
                    stand_has_branche=len(branches) > 0,
                    stand_has_required_branche=self.stand_has_required_branche(
                        branches
                    ),
                    merchant_has_required_branche=is_required,
                    merchant_has_evi=evi_merchant,
                )
                if evi_space_vars in illegal_combos:
                    return False

                evi_moving_vpl = AV(
                    market_has_unused_evi_space=self.market_info_delegate.market_has_unused_evi_space(),
                    prevent_evi=self.prevent_evi,
                    stand_has_evi=self.stand_has_evi(std),
                )
                if evi_moving_vpl in illegal_combos:
                    return False

            return True
        except Exception as e:
            print("error", e)
            traceback.print_exc(file=sys.stdout)

    def option_is_available(self, option):
        if "STW" in option:
            return False
        stands_not_available = (
            self.stands_reserved_for_expansion + self.stands_allocated
        )
        # stands_not_available = self.stands_allocated
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
        prefs=[],
        preferred=False,
        merchant_branche=None,
        evi_merchant=False,
        ignore_check_available=None,
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
            if valid:
                branche_valid_for_option = True
                if merchant_branche:
                    branche_valid_for_option = self.option_is_valid_branche(
                        option, merchant_branche, evi_merchant
                    )
                if ignore_check_available:
                    option = list(set(option) - set(ignore_check_available))
                if branche_valid_for_option and self.option_is_available_for_expansion(
                    option
                ):
                    valid_options.append(option)
        if preferred:
            return self.filter_preferred(valid_options, prefs)
        else:
            return valid_options

    def find_valid_cluster(
        self,
        stand_list,
        size=2,
        preferred=False,
        merchant_branche=None,
        mode="all",
        evi_merchant=False,
        ignore_reserved=False,
    ):
        """
        check all adjacent clusters of the requested size
        """
        valid_options = []
        for i, elem in enumerate(self.flattened_list):
            # an option is valid if it is present in de prio list
            option = self.flattened_list[i : i + size]
            if mode == "all":
                valid = all(elem in stand_list for elem in option)
            else:  # any
                valid = any(elem in stand_list for elem in option) and all(
                    isinstance(x, str) for x in option
                )
            if valid:
                branche_valid_for_option = True
                if merchant_branche:
                    branche_valid_for_option = self.option_is_valid_branche(
                        option, merchant_branche, evi_merchant
                    )
                if ignore_reserved:
                    if (
                        branche_valid_for_option
                        and self.option_is_available_for_expansion(option)
                    ):
                        valid_options.append(option)
                else:
                    if branche_valid_for_option and self.option_is_available(option):
                        valid_options.append(option)
        if preferred:
            return self.filter_preferred(valid_options, stand_list)
        else:
            return valid_options

    def find_valid_cluster_final_phase(
        self,
        stand_list,
        size=2,
        preferred=False,
        merchant_branche=None,
        anywhere=False,
        ignore_reserved=False,
    ):
        """
        check all adjacent clusters of the requested size
        """
        valid_options = []
        for i, elem in enumerate(self.flattened_list):
            # an option is valid if it is present in de prio list
            option = self.flattened_list[i : i + size]
            if anywhere:
                valid = all(isinstance(x, str) for x in option)
            else:
                valid = any(elem in stand_list for elem in option) and all(
                    isinstance(x, str) for x in option
                )
            if ignore_reserved:
                if valid and self.option_is_available_for_expansion(option):
                    valid_options.append(option)
            else:
                if valid and self.option_is_available(option):
                    valid_options.append(option)
        if preferred:
            return self.filter_preferred(valid_options, stand_list)
        else:
            return valid_options


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
