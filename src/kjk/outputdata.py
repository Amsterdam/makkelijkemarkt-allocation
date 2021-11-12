class StandsTypeError:
    pass

class MarketArangement:
    """
    A MarketArangement is responsible for producing the output JSON structure for KjK.
    For anexample see: 'fixtures/dapp_20211030/a_indeling.json'
    """

    def __init__(self, market_id=None, market_date=None):
        self.market_config = {}
        self.market_id = market_id
        self.market_date = market_date
        self.allocation_dict = {}
        self.rejection_list = {}

    def add_allocation(self, merchant_id=None, stand_ids=None, merchant_object=None):
        if type(stand_ids) != "list":
            raise StandsTypeError('market stands must be of type list') 
        if merchant_id in self.allocation_dict:
            allocation_obj = self.allocation_dict[merchant_id]
            allocation_obj['plaatsen'] + stand_ids
        else:
            allocation_obj = {
                "marktId": self.market_id,
                "ondernemer": merchant_object,
                "plaatsen": stand_ids,
                "marktDate": self.market_date,
                "erkenningsNummer": merchant_id
            }
            self.allocation_dict[merchant_id] = allocation_obj

    def add_rejection(self, merchant_id=None, reason_code=None, reason_txt=None, merchant_object=None):
        rejection_obj = {
            "marktId": self.market_id,
            "ondernemer": merchant_object,
            "reason": {
                "code": reason_code,
                "message": reason_txt
            },
            "marktDate": self.market_date,
            "erkenningsNummer": merchant_id
        }
        self.rejection_list.append(rejection_obj)

    def set_config(self, conf=None):
        self.market_config = conf

