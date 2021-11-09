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

        # create a dataframe with merchants attending the market
        self.merchants_df = self.df_for_attending_merchants()

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
        return pd.concat([df_1, df_2])

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
        return {}

