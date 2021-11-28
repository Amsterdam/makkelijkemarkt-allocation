import json
import redis


class MarketStandClusterFinder:

    """
    Find the best combination of market stands in a preference list from the merchant.
    The list is sorted by priority. (most desirable first) We do not want to allocate merchants if stands are not
    adjacent, in another market row or have an obstakel in between.
    """

    def __init__(self, data, obstacles, branches_dict, evi_dict):
        self.stands_allocated = []
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
                    except KeyError as e:
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

    def set_stands_allocated(self, allocated_stands):
        self.stands_allocated += allocated_stands

    def _process_obstacle_dict(self, obs):
        d = {}
        for ob in obs:
            d[ob["kraamA"]] = ob["obstakel"]
        return d

    def get_neighbours_for_stand_id(self, stand_id):
        """
        Get the neighbouring stand for a stand_id.
        Can be used to validate an allocation of multiple stands.
        """
        try:
            return self.stands_linked_list[stand_id]
        except KeyError as e:
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

    def option_is_valid_branche(self, option, merchant_branche, evi_merchant):
        """
        check if a merchant is trying to move to a branche incompatible stand
        """
        try:
            for std in option:
                branches = self.branches_dict[std]
                if len(branches) > 0 and len(merchant_branche) > 0:
                    if merchant_branche[0] not in branches:
                        return False
                if evi_merchant:
                    if "eigen-materieel" not in self.evi_dict[std]:
                        return False
                else:
                    return "eigen-materieel" not in self.evi_dict[std]
        except KeyError as e:
            pass
        except TypeError as e:
            pass
        return True

    def option_is_available(self, option):
        return not any(elem in option for elem in self.stands_allocated)

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
                if branche_valid_for_option and self.option_is_available(option):
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
                if branche_valid_for_option and self.option_is_available(option):
                    valid_options.append(option)
        if preferred:
            return self.filter_preferred(valid_options, stand_list)
        else:
            return valid_options

    def find_valid_cluster_final_phase(
        self, stand_list, size=2, preferred=False, merchant_branche=None, anywhere=False
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
            if valid and self.option_is_available(option):
                valid_options.append(option)
        if preferred:
            return self.filter_preferred(valid_options, stand_list)
        else:
            return valid_options


class DebugRedisClient:
    """
    This a debug only object, it will insert the json file into a local redis
    so the allocation result can be displayed in the KjK application as a concept allocation
    this class will use the redis KEY 'RESULT_1' and the result url http://127.0.0.1:8080/job/1/
    """

    def __init__(self):
        REDIS_HOST = "127.0.0.1"
        REDIS_PORT = 6379
        REDIS_PASSWORD = "Salmagundi"

        self.r = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD
        )
        res = self.r.delete("RESULT_1")

    def insert_test_result(self, allocation_json):
        f = open(allocation_json, "r")
        data = f.read()
        self.r.set("RESULT_1", data)
        f.close()
        print("-" * 60)
        print("View the results here:")
        print("http://127.0.0.1:8080/job/1/")
        print("-" * 60)
