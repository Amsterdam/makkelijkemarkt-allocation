import json
from pprint import pprint
from kjk.base import BaseDataprovider


class DataproviderGetterMixin:
    def get_obstacles(self):
        return self.data["obstakels"]

    def get_market_blocks(self):
        return self.data["paginas"]

    def get_market_date(self):
        return self.data["marktDate"]

    def get_market(self):
        return self.data["markt"]

    def get_merchants(self):
        return self.data["ondernemers"]

    def get_market_locations(self):
        return self.data["marktplaatsen"]

    def get_rsvp(self):
        return self.data["aanmeldingen"]

    def get_a_list(self):
        return self.data["aLijst"]

    def get_attending(self):
        return self.data["aanwezigheid"]

    def get_branches(self):
        return self.data["branches"]

    def get_preferences(self):
        return self.data["voorkeuren"]

    def get_market_id(self):
        return self.data["marktId"]

    def get_market_date(self):
        return self.data["marktDate"]


class MockDataprovider(DataproviderGetterMixin, BaseDataprovider):
    """
    Use this class to build mocked markets for unit/scenario testing

    # start with a market based on fixture:
    mock_market = MockDataprovider("../fixtures/test_input.json")

    # add merchants to the market:
    mock_market.add_merchant(erkenningsNummer='1123456',
                           plaatsen=['1', '2'],
                           status='vpl',
                           sollicitatieNummer="123",
                           description='Frank Zappa',
                           voorkeur={"branches": ['101-afg'], "maximum": 3, "minimum": 2, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

    # add market stands to the mock:
    mock_market.add_stand(plaatsId='1', branches=['101-agf'], properties=['boom'], verkoopinrichting=[])

    # add branches if required:
    mock_market.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

    # add rsvp if rquired:
    mock_market.add_rsvp(erkenningsNummer='112345', attending=True)

    # commit the mock data
    mock_market.sut.mock()

    # use it to test the Allocator
    allocator = Allocator(mock_market)
    market_allocation = allocation = allocator.get_allocation()
    # assert market_allocation now

    """

    def __init__(self, json_file):
        self.input_file = json_file
        f = open(self.input_file, "r")
        self.data = json.load(f)
        f.close()

        # start with an empty market config
        self.data["ondernemers"] = []
        self.data["branches"] = []
        self.data["marktplaatsen"] = []
        self.data["paginas"] = []
        self.data["obstakels"] = []
        self.data["aanmeldingen"] = []
        self.data["aLijst"] = []
        self.data["voorkeuren"] = []

        # mock data not loaded yet
        self.mocked = False

    def mock(self):
        self.mocked = True

    def load_data(self):
        if not self.mocked:
            print("WARNING: mock objects not loaded!")

    def add_page(self, plaats_list=[]):
        d = {
            "title": "Test block",
            "indelingslijstGroup": [
                {
                    "class": "block-left",
                    "title": "2-22",
                    "landmarkTop": "Mauritskade",
                    "landmarkBottom": "Pieter Vlamingstraat",
                    "plaatsList": plaats_list,
                }
            ],
        }
        self.data["paginas"].append(d)

    def add_pref(self, **kwargs):
        """
        erkenningsNummer: "4000175070",
        plaatsId: "247",
        priority: 1,
        """
        self.data["voorkeuren"].append(kwargs)

    def add_rsvp(self, **kwargs):
        self.data["aanmeldingen"].append(kwargs)

    def add_merchant(self, **kwargs):
        self.data["ondernemers"].append(kwargs)

    def update_merchant(self, **kwargs):
        """update merchant based on erkenningsNummer"""
        index = None
        for i, m in enumerate(self.data["ondernemers"]):
            if m["erkenningsNummer"] == kwargs["erkenningsNummer"]:
                index = i
        if index is not None:
            self.data["ondernemers"][index] = kwargs

    def add_stand(self, **kwargs):
        self.data["marktplaatsen"].append(kwargs)

    def add_obstacle(self, **kwargs):
        """
        kraamA: "245",
        kraamB: "247",
        obstakel: [
            "loopje"
        ]
        """
        self.data["obstakels"].append(kwargs)

    def add_branche(self, **kwargs):
        """
        brancheId : str
        number : int
        description : str
        color : str
        verplicht : bool
        maximumPlaatsen : int
        """
        self.data["branches"].append(kwargs)


class FixtureDataprovider(DataproviderGetterMixin, BaseDataprovider):
    """A fixture based dataprovider"""

    def __init__(self, json_file):
        self.input_file = json_file

    def load_data(self):
        f = open(self.input_file, "r")
        self.data = json.load(f)
        f.close()
        return self.data


if __name__ == "__main__":
    dp = FixtureDataprovider("fixtures/dapp_20211030/a_input.json")
