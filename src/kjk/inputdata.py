import json
from pprint import pprint

class BaseDataprovider:
    """
    Defines an interface to provide data for the Allocator object (kjk.allocation.Allocator)
    Market data should contain the following collections:
        marktDate, marktId, paginas, rows, branches, voorkeuren, naam, obstakels, aanmeldingen 
        markt, aLijst, ondernemers, aanwezigheid, marktplaatsen
    see: 'fixtures/dapp_20211030/a_input.json' for an anonimyzed example of a real world scenario
    """

    def load_data(self):
        raise NotImplementedError

    def get_market(self):
        raise NotImplementedError

    def get_market_locations(self):
        raise NotImplementedError

    def get_market_locations(self):
        raise NotImplementedError

    def get_rsvp(self):
        raise NotImplementedError

    def get_a_list(self):
        raise NotImplementedError

    def get_attending(self):
        raise NotImplementedError

    def get_branches(self):
        raise NotImplementedError

    def get_preferences(self):
        raise NotImplementedError

    def get_market_date(self):
        raise NotImplementedError

    def get_market_id(self):
        raise NotImplementedError

    def get_market_date(self):
        raise NotImplementedError

    def get_market_blocks(self):
        raise NotImplementedError

    def get_obstacles(self):
        raise NotImplementedError


class FixtureDataprovider(BaseDataprovider):
    """A fixture based dataprovider"""
    def __init__(self, json_file):
        self.input_file = json_file

    def load_data(self):
        f = open(self.input_file, 'r')
        self.data = json.load(f)
        f.close()
        return self.data

    def get_obstacles(self):
        return self.data['obstakels']

    def get_market_blocks(self):
        return self.data['paginas']

    def get_market_date(self):
        return self.data['marktDate']

    def get_market(self):
        return self.data['markt']

    def get_merchants(self):
        return self.data['ondernemers']

    def get_market_locations(self):
        return self.data['marktplaatsen']

    def get_rsvp(self):
        return self.data['aanmeldingen']

    def get_a_list(self):
        return self.data['aLijst']

    def get_attending(self):
        return self.data['aanwezigheid']

    def get_branches(self):
        return self.data['branches']

    def get_preferences(self):
        return self.data['voorkeuren']

    def get_market_id(self):
        return self.data['marktId']

    def get_market_date(self):
        return self.data['marktDate']


if __name__ == "__main__":
    dp = FixtureDataprovider('fixtures/dapp_20211030/a_input.json')

