import json

class StandsTypeError(BaseException):
    pass

BRANCHE_FULL = {
    "code": 1,
    "message": 'Alle marktplaatsen voor deze branche zijn reeds ingedeeld.'
}
ADJACENT_UNAVAILABLE = {
    "code": 2,
    "message": 'Geen geschikte locatie gevonden met huidige voorkeuren.'
};
MINIMUM_UNAVAILABLE = {
    "code": 3,
    "message": 'Minimum aantal plaatsen niet beschikbaar.'
}
MARKET_FULL  = {
    "code": 4,
    "message": 'Alle marktplaatsen zijn reeds ingedeeld.'
}

class MarketArrangement:
    """
    A MarketArrangement is responsible for producing the output JSON structure for KjK.
    For anexample see: 'fixtures/dapp_20211030/a_indeling.json'
    """

    def __init__(self, market_id=None, market_date=None):
        self.output = {}
        self.market_config = {}
        self.market_id = market_id
        self.market_date = market_date
        self.allocation_dict = {}
        self.rejection_list = []
        self.branches = []
        self.market_blocks = []
        self.rsvp = []
        self.obstacles = []
        self.market_positions = []
        self.merchants = []

    def add_allocation(self, merchant_id=None, stand_ids=None, merchant_object=None):
        if type(stand_ids) is not list:
            raise StandsTypeError('market stands must be of type list') 
        if merchant_id in self.allocation_dict:
            allocation_obj = self.allocation_dict[merchant_id]
            allocation_obj['plaatsen'] += stand_ids
        else:
            allocation_obj = {
                "marktId": self.market_id,
                "ondernemer": merchant_object,
                "plaatsen": stand_ids,
                "marktDate": self.market_date,
                "erkenningsNummer": merchant_id
            }
            self.allocation_dict[merchant_id] = allocation_obj

    def add_rejection(self, merchant_id=None, reason=None, merchant_object=None):
        rejection_obj = {
            "marktId": self.market_id,
            "ondernemer": merchant_object,
            "reason": reason,
            "marktDate": self.market_date,
            "erkenningsNummer": merchant_id
        }
        self.rejection_list.append(rejection_obj)

    def set_config(self, conf=None):
        self.market_config = conf

    def set_merchants(self, merchants):
        self.merchants = merchants

    def set_branches(self, branches):
        self.branches = branches

    def set_market_positions(self, pos):
        self.market_positions = pos

    def set_market_blocks(self, blocks):
        self.market_blocks = blocks

    def set_obstacles(self, obs):
        self.obstacles = obs

    def set_rsvp(self, rsvp):
        self.rsvp = rsvp

    def to_data(self):
        self.output['naam'] = "?"
        self.output['marktId'] = self.market_id
        self.output['marktDate'] = self.market_date
        self.output['branches'] = self.branches
        self.output['paginas'] = self.market_blocks
        self.output['aanmeldingen'] = self.rsvp
        self.output['obstakels'] = self.obstacles
        self.output['marktplaatsen'] = self.market_positions
        self.output['ondernemers'] = self.merchants
        self.output['markt'] = self.market_config
        self.output['toewijzingen'] = list(self.allocation_dict.values())
        self.output['afwijzingen'] = self.rejection_list
        return self.output

    def to_json_file(self, file_name="test_output.json"):
        f = open(file_name, "w")
        json.dump(self.to_data(), f, indent = 4)
        f.close()
        return file_name



