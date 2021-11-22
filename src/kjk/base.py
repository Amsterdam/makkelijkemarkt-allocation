from pprint import pprint
import pandas as pd
from datetime import date
from kjk.outputdata import MarketArrangement
from kjk.utils import MarketStandClusterFinder

pd.options.mode.chained_assignment = 'raise'


# dataframe views for debugging
EXPANDERS_VIEW = [ "description", "voorkeur.maximum", "voorkeur.minimum", "plaatsen", "pref", "voorkeur.anywhere"]
MERCHANTS_SORTED_VIEW = ["erkenningsNummer", "sollicitatieNummer", 
                         "pref", "voorkeur.branches", 
                         "voorkeur.minimum", "voorkeur.maximum"]
ALIST_VIEW = ["erkenningsNummer", "description" ,"alist", "sollicitatieNummer"]
BRANCHE_VIEW = ["erkenningsNummer", "description" ,"voorkeur.branches", "branche_required"]

class VPLCollisionError(BaseException):
    """this will be raised id two VPL merchants claim the same market position. (should never happen)"""
    pass


class MerchantNotFoundError(BaseException):
    """this will be raised id a merchant id can not be found in the input data. (should never happen)"""
    pass

class MerchantDequeueError(BaseException):
    """this will be raised id a merchant id can not be removed from the queue (should never happen)"""
    pass


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


class BaseAllocator:
    """
    Allocator object will take a single dataprovider argument and produce a market.
    Injected dadaproviders should implement the inputdata.BaseDataprovider interface
    to ensure compatibility.
    Mock-dataproviders can be userd for testing and API-based dataprovider for ACC and PRD envs.
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
        self.market_blocks = dp.get_market_blocks()
        self.obstacles= dp.get_obstacles()

        # market id and date
        self.market_id = dp.get_market_id()
        self.market_date = dp.get_market_date()

        # output object
        self.market_output = MarketArrangement(market_id=self.market_id, market_date=self.market_date)
        self.market_output.set_config(self.market)
        self.market_output.set_branches(self.branches)
        self.market_output.set_market_positions(self.open_positions)
        self.market_output.set_merchants(self.merchants)
        self.market_output.set_market_blocks(self.market_blocks)
        self.market_output.set_obstacles(self.obstacles)
        self.market_output.set_rsvp(self.rsvp)

        # we need a python date for checking periodic absence of vpl's
        self.market_date = date.fromisoformat(dp.get_market_date())

        # merchants objects by erkennings nummer
        self.merchants_dict = self.create_merchant_dict()

        # dataframes for easy access
        self.merchants_df = pd.json_normalize(self.merchants)
        self.raw_merchants_df = pd.json_normalize(self.merchants)
        self.positions_df = pd.json_normalize(self.open_positions)
        self.prefs_df = pd.json_normalize(self.prefs)
        self.rsvp_df = pd.json_normalize(self.rsvp)
        self.branches_df = pd.json_normalize(self.branches)
        self.a_list_df = pd.json_normalize(self.a_list)

        # data frame to hold merchants wo want extra stands
        # they will be popped from teh main qeueu when allocated
        # this data will be used for later itterations
        self.expanders_df = None

        # remove duplicate erkenningsNummers from nerchants df
        # not sure but we just keep the first?
        self.merchants_df.drop_duplicates(subset="erkenningsNummer", keep="first", inplace=True)

        # create a dataframe with merchants attending the market
        # and create a positions dataframe
        # these dataframes will be used in the allocation
        self.cluster_finder = MarketStandClusterFinder(dp.get_market_blocks(), dp.get_obstacles())
        self.prepare_merchants()
        self.prepare_stands()

        # save to text for manual debugging
        self.merchants_df.to_markdown("merchants.md")

    def create_merchant_dict(self):
        d = {}
        for m in self.merchants:
            d[m['erkenningsNummer']] = m;
        return d

    def merchant_object_by_id(self, merchant_id):
        try:
            return self.merchants_dict[merchant_id]
        except KeyError as e:
            raise MerchantNotFoundError(f"mechant not found: {merchant_id}")

    def prepare_merchants(self):
        """prepare the merchants list for allocation"""
        self.df_for_attending_merchants()
        self.add_prefs_for_merchant()
        self.add_alist_status_for_merchant()
        self.add_required_branche_for_merchant()
        self.merchants_df.set_index("erkenningsNummer", inplace=True)
        self.merchants_df['erkenningsNummer'] = self.merchants_df.index

    def prepare_stands(self):
        """prepare the stands list for allocation"""
        def required(x):
            try:
                return self.get_required_for_branche(x)
            except KeyError as e:
                return "unknown"
        is_required = self.positions_df['branches'].apply(required)
        self.positions_df["required"] = is_required
        self.positions_df.set_index("plaatsId", inplace=True)
        self.positions_df['plaatsId'] = self.positions_df.index

        try:
            def is_inactive(x):
                if x == True:
                    return False
                return True
            active = self.positions_df['inactive'].apply(is_inactive)
            self.positions_df = self.positions_df[active]
        except KeyError as e:
            # No inactive stand found in cofiguration
            pass

    def get_required_for_branche(self, b):
        try:
            if len(b) == 0:
                return "no"
        except TypeError as e:
            return "no"
        # assumption:
        # if more than one branche per stand always means bak?
        if len(b) >= 1:
            if "bak" in b:
                return "yes"
            result = self.branches_df[self.branches_df["brancheId"] == b[0]]
            if len(result) > 0 and result.iloc[0]['verplicht'] == True:
                return "yes"
            else:
                return "no"
        return "unknown"

    def get_prefs_for_merchant(self, merchant_number):
        """get position pref for merchant_number (erkenningsNummer)"""
        result_df = self.prefs_df[self.prefs_df['erkenningsNummer'] == merchant_number].copy()
        result_df.sort_values(by=['priority'], inplace=True)
        plaats = result_df['plaatsId'].to_list()
        return plaats

    def get_willmove_for_merchant(self, merchant_number):
        """check if this merchant wants to move (only relevant for vpl) . merchant_number (erkenningsNummer)"""
        result_df = self.prefs_df[self.prefs_df['erkenningsNummer'] == merchant_number]
        plaats = result_df['plaatsId'].to_list()
        if len(plaats) > 0:
            return "yes"
        else:
            return "no"

    def add_alist_status_for_merchant(self):
        def prefs(x):
            try:
                result_df = self.a_list_df[self.a_list_df['erkenningsNummer'] == x].copy()
                return len(result_df) > 0
            except KeyError as e:
                return False
        self.merchants_df['alist'] = self.merchants_df['erkenningsNummer'].apply(prefs)

    def add_required_branche_for_merchant(self):
        def required(x):
            try:
                return self.get_required_for_branche(x)
            except KeyError as e:
                return "unknown"
        is_required = self.merchants_df['voorkeur.branches'].apply(required)
        self.merchants_df["branche_required"] = is_required

    def add_prefs_for_merchant(self):
        """add position preferences to the merchant dataframe"""
        def prefs(x):
            try:
                return self.get_prefs_for_merchant(x)
            except KeyError as e:
                return []
        self.merchants_df['pref'] = self.merchants_df['erkenningsNummer'].apply(prefs)

        def will_move(x):
            try:
                return self.get_willmove_for_merchant(x)
            except KeyError as e:
                return "no"
        self.merchants_df['will_move'] = self.merchants_df['erkenningsNummer'].apply(will_move)

        def wants_to_expand(x):
            if x['status'] == "vpl":
                return len(x['plaatsen']) < x['voorkeur.maximum']
            else:
                return False
        self.merchants_df['wants_expand'] = self.merchants_df.apply(wants_to_expand, axis=1)

    def df_for_attending_merchants(self):
        """
        Wich merchants are actually attending the market?
        - vpl and tvpl only have to tell when they are NOT attending
        - non vpl (tvplz, soll and exp) do have to attend.
        """
        def is_attending_market(x):
            try:
                att = self.get_rsvp_for_merchant(x)
                if att == True:
                    return "yes"
                elif att == False:
                    return "no"
                else:
                    return "na"
            except KeyError as e:
                return "na"
        self.merchants_df['attending'] = self.merchants_df['erkenningsNummer'].apply(is_attending_market)
        df_1 = self.merchants_df.query("attending != 'no' & (status == 'vpl' | status == 'tvlp')")
        df_2 = self.merchants_df.query("attending == 'yes' & (status != 'vpl' & status != 'tvlp')")
        self.merchants_df = pd.concat([df_1, df_2])

        def check_absent(x):
            if x['voorkeur.absentUntil'] != None and x['voorkeur.absentFrom']:
                from_str = x['voorkeur.absentFrom']
                from_date = date.fromisoformat(from_str)
                until_str = x['voorkeur.absentUntil']
                until_date = date.fromisoformat(until_str)
                if from_date <= self.market_date <= until_date:
                    return False
            return True
        df = self.merchants_df[['voorkeur.absentFrom', 'voorkeur.absentUntil']].apply(check_absent, axis=1)
        self.merchants_df = self.merchants_df[df]

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

    def get_expander_for_branche(self, branche, status=None):
        """get all expander for a given branche for this market"""
        def has_branch(x):
            try:
                if branche in x:
                    return True
            except TypeError as e:
                # nobranches == nan in dataframe
                pass
            return False
        has_branch = self.expanders_df['voorkeur.branches'].apply(has_branch)
        result_df = self.expanders_df[has_branch][["erkenningsNummer", "status"]]
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

    def get_baking_positions_df(self):
        """get all baking positions for this market """
        def has_bak(x):
            if "bak" in x:
                return True
            return False
        has_bak_df = self.positions_df['branches'].apply(has_bak)
        result_df = self.positions_df[has_bak_df]
        return result_df

    def get_rsvp_for_merchant(self, merchant_number):
        """boolean, Is this mechant attending this market?"""
        result_df = self.rsvp_df[self.rsvp_df['erkenningsNummer'] == merchant_number]
        if len(result_df) == 1:
            return result_df.iloc[0]['attending']
        return None

    def get_evi_stands(self):
        """ return a dataframe with evi stands"""
        def has_evi(x):
            if 'eigen-materieel' in x:
                return True
            else:
                return False
        hasevi = self.positions_df['verkoopinrichting'].apply(has_evi)
        return self.positions_df[hasevi]

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

    def dequeue_marchant(self, merchant_id):
        self.merchants_df.drop(merchant_id, inplace=True)

    def dequeue_market_stand(self, stand_id):
        self.positions_df.drop(stand_id, inplace=True)

    def num_merchants_in_queue(self):
        return len(self.merchants_df)

    def num_stands_in_queue(self):
        return len(self.positions_df)

    def get_branches_for_stand(self, stand_id):
        stand = self.positions_df.query(f"plaatsId == '{stand_id}'")
        if len(stand) != 1:
            return []
        return stand['branches'].iloc[0]
    
    def get_stand_for_branche(self, branche):
        def is_branche(x):
            if branche in x:
                return True
            return False
        stands = self.positions_df['branches'].apply(is_branche)
        return self.positions_df[stands]
