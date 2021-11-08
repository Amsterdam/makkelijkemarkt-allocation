class Allocator:

    def __init__(self, data_provider):
        dp = data_provider
        dp.load_data()
        self.market = dp.get_market()
        self.merchants = dp.get_merchants()
        self.rsvp = dp.get_rsvp()
        self.a_list = dp.get_a_list()
        self.attending = dp.get_attending()
        self.branches = dp.get_branches()

    def get_allocation(self):
        return {}

