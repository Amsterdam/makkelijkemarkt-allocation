import json
from pprint import pprint

class BaseDataProvider:

    # marktDate 
    # marktId 
    # paginas 
    # rows
    # branches 
    # voorkeuren 
    # naam
    # obstakels
    # aanmeldingen 
    # markt
    # aLijst 
    # ondernemers 
    # aanwezigheid 
    # marktplaatsen

    def load_data(self):
        raise NotImplementedError

    def get_market(self):
        raise NotImplementedError
    
    def get_market_locations(self):
        raise NotImplementedError


class FixtureDataprovider(BaseDataProvider):
    def __init__(self, json_file):
        self.input_file = json_file

    def load_data(self):
        f = open(self.input_file, 'r')
        self.data = json.load(f)
        f.close()
        return self.data

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

        

if __name__ == "__main__":
    dp = FixtureDataprovider('fixtures/dapp_20211030/a_input.json')














