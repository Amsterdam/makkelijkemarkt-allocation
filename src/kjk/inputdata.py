import json
from pprint import pprint
from kjk.base import BaseDataprovider


class DataproviderGetterMixin:

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


class MockDataprovider(DataproviderGetterMixin):

    def __init__(self, json_file):
        self.input_file = json_file
        f = open(self.input_file, 'r')
        self.data = json.load(f)
        f.close()

        # start with an empty market config
        self.data['ondernemers'] = []
        self.data['branches'] = []
        self.data['marktplaatsen'] = []
        self.data['paginas'] = []
        self.data['obstakels'] = []
        self.data['aanmeldingen'] = []
        self.data['aLijst'] = []
        self.data['voorkeuren'] = []

        # mock data not loaded yet
        self.mocked = False

    def mock(self):
        self.mocked = True

    def load_data(self):
        if not self.mocked:
            print("WARNING: mock objects not loaded!")

    def add_rsvp(self, **kwargs):
        self.data['aanmeldingen'].append(kwargs)

    def add_merchants(self, **kwargs):
        kwargs['voorkeur'].update({"absentFrom":"", "absentUntil":""})
        self.data['ondernemers'].append(kwargs)

    def add_stand(self, **kwargs):
        self.data['marktplaatsen'].append(kwargs)

    def add_branche(self, **kwargs):
        """
        brancheId : str
        number : int
        description : str
        color : str
        verplicht : bool
        maximumPlaatsen : int
        """
        self.data['branches'].append(kwargs)


class FixtureDataprovider(BaseDataprovider, DataproviderGetterMixin):
    """A fixture based dataprovider"""
    def __init__(self, json_file):
        self.input_file = json_file

    def load_data(self):
        f = open(self.input_file, 'r')
        self.data = json.load(f)
        f.close()
        return self.data

if __name__ == "__main__":
    dp = FixtureDataprovider('fixtures/dapp_20211030/a_input.json')

