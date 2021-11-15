class MarketStandClusterFinder:

    """
    Find the best combination of market stands in a preference list from the merchant.
    The list is sorted by priority. (most desirable first) We do not want to allocate merchants if stands are not
    adjacent, in another market row or have an obstakel in between.
    """
    def __init__(self, data):
        self.flattened_list = []
        self.stands_linked_list = {}
        for k in data:
            for gr in k['indelingslijstGroup']:
                pl = gr['plaatsList']
                self.flattened_list.append(None)
                self.flattened_list += pl
                for i, stand_nr in enumerate(pl):
                    if i-1 >= 0:
                        _prev = pl[i-1]
                    else:
                        _prev = None
                    _mid = pl[i]
                    try:
                        _next = pl[i+1]
                    except IndexError:
                        _next = None
                    self.stands_linked_list[_mid] = {"prev": _prev, "next": _next}
        self.flattened_list.append(None)

    def filter_preferred(self, valid_options, stand_list):
        """
        return the option containing the highest prio stand (lowest list index)
        """
        for std in stand_list:
            for option in valid_options:
                if std in option:
                    return option

    def find_valid_cluster(self, stand_list, size=2, preferred=False):
        """
        check all adjacent clusters of the requested size
        """
        valid_options = []
        for i, elem in enumerate(self.flattened_list):
            # an option is valid if it i present in de prio list
            option = self.flattened_list[i:i+size]
            valid =  all(elem in stand_list for elem in option)
            if valid:
                valid_options.append(option)
        if preferred:
            return self.filter_preferred(valid_options, stand_list)
        else:
            return valid_options

