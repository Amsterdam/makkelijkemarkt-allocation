from pprint import pprint
import pandas as pd


class VPLCollisionError(BaseException):
    """this will be raised id two VPL merchants claim the same market position. (should never happen)"""
    pass

class Allocator:
    """
    Allocator object will take a single dataprovider argument and produce a market.
    Injected dadaproviders should implement the inputdata.BaseDataprovider interface
    to ensure compatibility.
    Mock-dataproviders can be userd for testing and API-based dataprovider fpor ACC and PRD envs.
    """

    def __init__(self, data_provider):
        """Accept the dataprovider and populate the data model"""
        dp = data_provider
        dp.load_data()

        # raw data
        self.market = dp.get_market()
        self.merchants = dp.get_merchants()
        self.rsvp = dp.get_rsvp()
        self.a_list = dp.get_a_list()
        self.attending = dp.get_attending()
        self.branches = dp.get_branches()
        self.prefs = dp.get_preferences()
        self.open_positions = dp.get_market_locations()

        # dataframes for easy access
        self.merchants_df = pd.json_normalize(self.merchants)
        self.positions_df = pd.json_normalize(self.open_positions)
        self.prefs_df = pd.json_normalize(self.prefs)
        self.rsvp_df = pd.json_normalize(self.rsvp)
        self.branches_df= pd.json_normalize(self.branches)

        # create a dataframe with merchants attending the market
        # and create a positions dataframe
        # these dataframes will be used in the allocation
        self.prepare_merchants()
        self.prepare_stands()

    def prepare_merchants(self):
        """prepare the merchants list for allocation"""
        self.df_for_attending_merchants()
        self.add_prefs_for_merchant()

    def prepare_stands(self):
        """prepare the stands list for allocation"""
        def required(x):
            return self.get_required_for_branche(x)
        is_required = self.positions_df['branches'].apply(required)
        self.positions_df["required"] = is_required

    def get_required_for_branche(self, b):
        if len(b) == 0:
            return "no"
        # assumption:
        # if more than one branche per stand alwyas means bak?
        if len(b) >= 1:
            if "bak" in b:
                return "yes"
            result = self.branches_df[self.branches_df["brancheId"] == b[0]]
            if result.iloc[0]['verplicht']:
                return "yes"
            else:
                return "no"
        return "unknown"

    def get_prefs_for_merchant(self, merchant_number):
        """get position pref for merchant_number (erkenningsNummer)"""
        result_df = self.prefs_df[self.prefs_df['erkenningsNummer'] == merchant_number]
        plaats = result_df['plaatsId'].to_list()
        prio = result_df['priority'].to_list()
        return [plaats, prio]

    def add_prefs_for_merchant(self):
        """add position preferences to the merchant dataframe"""
        def prefs(x):
            return self.get_prefs_for_merchant(x)
        self.merchants_df['pref'] = self.merchants_df['erkenningsNummer'].apply(prefs)

    def df_for_attending_merchants(self):
        """
        Wich merchants are actually attending the market?
        - vpl only have to tell when they are NOT attending
        - non vpl (soll and exp) do have to attend.
        """
        def is_attending_market(x):
            att = self.get_rsvp_for_merchant(x)
            if att == True:
                return "yes"
            elif att == False:
                return "no"
            else:
                return "na"
        self.merchants_df['attending'] = self.merchants_df['erkenningsNummer'].apply(is_attending_market)
        d = self.merchants_df
        df_1 = d[(d['attending'] != "no") & (d['status'] == "vpl")]
        df_2 = d[(d['attending'] == "yes") & (d['status'] != "vpl")]
        self.merchants_df = pd.concat([df_1, df_2])

    def get_vpl_for_position(self, position):
        """return a merchant number for a fixed position, reurn None is no merchant found"""
        def num_positions(x):
            if position in x:
                return True
            return False
        has_positions = self.merchants_df['plaatsen'].apply(num_positions)
        result_df = self.merchants_df[has_positions]
        if len(result_df) == 1:
            return result_df.iloc[0]['erkenningsNummer']
        if len(result_df) > 1:
            raise VPLCollisionError(f"more than one vpl merchant for position {position}")
        return None

    def get_merchant_for_branche(self, branche, status=None):
        """get all merchants for a given branche for this market"""
        def has_branch(x):
            try:
                if branche in x:
                    return True
            except TypeError as e:
                # nobranches == nan in dataframe
                pass
            return False
        has_branch = self.merchants_df['voorkeur.branches'].apply(has_branch)
        result_df = self.merchants_df[has_branch][["erkenningsNummer", "status"]]
        if status is not None:
            result_df = result_df[result_df["status"] == status]
        result_df = result_df["erkenningsNummer"]
        return result_df.to_list()

    def get_baking_positions(self):
        """get all baking positions for this market """
        def has_bak(x):
            if "bak" in x:
                return True
            return False
        has_bak_df = self.positions_df['branches'].apply(has_bak)
        result_df = self.positions_df[has_bak_df]['plaatsId']
        return result_df.to_list()

    def get_rsvp_for_merchant(self, merchant_number):
        """boolean, Is this mechant attending this market?"""
        result_df = self.rsvp_df[self.rsvp_df['erkenningsNummer'] == merchant_number]
        if len(result_df) == 1:
            return result_df.iloc[0]['attending']
        return None

    def get_merchants_with_evi(self, status=None):
        """return list of merchant numbers with evi, optionally filtered by status ('soll', 'vpl', etc)"""
        def has_evi(x):
            try:
                if "eigen-materieel" in x:
                    return True
            except TypeError as e:
                # nobranches == nan in dataframe
                pass
            return False
        has_evi = self.merchants_df['voorkeur.verkoopinrichting'].apply(has_evi)
        result_df = self.merchants_df[has_evi][["erkenningsNummer", "status"]]
        if status is not None:
            result_df = result_df[result_df["status"] == status]
        result_df = result_df["erkenningsNummer"]
        return result_df.to_list()

    def get_allocation(self):
        """
        1. Deel VPHs die niet willen verplaatsen in op hun eigen vaste plaatsen;
        2. Deel VPH's in die willen verplaatsen (bereken door of dit succesvol verloopt,
           anders terugvallen op eigen plaats; Als één of meerdere bestemmingsplaatsen van een ándere verplaatsende VPH zijn,
           wordt eerst gecontroleerd of laatstgenoemde nog wel ingedeeld kan worden als eerstgenoemde daar wordt ingedeeld.);
        3. Deel ondernemers in die opereren in dezelfde branche als de vrijgekomen plaatsen.
           Deze groep kan bestaan uit VPHs die willen verplaatsen en sollicitanten.
           Als er meer ondernemers zijn dan beschikbare plaatsen, dan worden de resterende ondernemers afgewezen.
        4. Resterende verplichte brancheplaatsen worden vanaf nu behandeld als normale, branchevrije plaatsen.
        5. Deel ondernemers in met een BAK. Ook dit kunnen zowel verplaatsende VPHs als sollicitanten zijn.
           Als er meer BAK ondernemers zijn dan beschikbare BAK plaatsen, dan worden de resterende ondernemers afgewezen.
        6. Resterende BAK plaatsen worden vanaf nu behandeld als normale plaatsen.
        7. Deel ondernemers in met een EVI. Ook dit kunnen zowel verplaatsende VPHs als sollicitanten zijn.
           Als er meer EVI ondernemers zijn dan beschikbare EVI plaatsen, dan worden de resterende ondernemers afgewezen.
        8. Resterende EVI plaatsen worden vanaf nu behandeld als normale plaatsen.
        9. Deel de overgebleven sollicitanten in.


        En dan nog, de uitbreidingen, de plaatsvoorkeuren met prio, vervangers, afwezigheid voor periode.
        """
        print(self.positions_df)
        print(self.merchants_df)
        return {}


if __name__ == "__main__":
    from inputdata import FixtureDataprovider
    dp = FixtureDataprovider("../../fixtures/dapp_20211030/a_input.json")
    a = Allocator(dp)
    a.get_allocation()
    a.prepare_stands()

