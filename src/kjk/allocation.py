from pprint import pprint
import pandas as pd
from datetime import date
from outputdata import MarketArrangement

pd.options.mode.chained_assignment = 'raise'

class VPLCollisionError(BaseException):
    """this will be raised id two VPL merchants claim the same market position. (should never happen)"""
    pass


class MerchantNotFoundError(BaseException):
    """this will be raised id a merchant id can not be found in the input data. (should never happen)"""
    pass


class Allocator:
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

        # market id and date
        self.market_id = dp.get_market_id()
        self.market_date = dp.get_market_date()

        # we need a python date for checking periodic absence of vpl's
        self.market_date = date.fromisoformat(dp.get_market_date())

        # merchants objects by erkennings nummer
        self.merchants_dict = self.create_merchant_dict()

        # dataframes for easy access
        self.merchants_df = pd.json_normalize(self.merchants)

        df = self.merchants_df
        ids = df["erkenningsNummer"]
        dubb = df[ids.isin(ids[ids.duplicated()])]
        print(">>>> ", dubb)
        print("len ", len(dubb))

        self.positions_df = pd.json_normalize(self.open_positions)
        self.prefs_df = pd.json_normalize(self.prefs)
        self.rsvp_df = pd.json_normalize(self.rsvp)
        self.branches_df= pd.json_normalize(self.branches)

        # create a dataframe with merchants attending the market
        # and create a positions dataframe
        # these dataframes will be used in the allocation
        self.prepare_merchants()
        self.prepare_stands()

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
        self.merchants_df.set_index("erkenningsNummer", inplace=True)
        self.merchants_df['erkenningsNummer'] = self.merchants_df.index

    def prepare_stands(self):
        """prepare the stands list for allocation"""
        def required(x):
            return self.get_required_for_branche(x)
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

    def add_prefs_for_merchant(self):
        """add position preferences to the merchant dataframe"""
        def prefs(x):
            return self.get_prefs_for_merchant(x)
        self.merchants_df['pref'] = self.merchants_df['erkenningsNummer'].apply(prefs)

        def will_move(x):
            return self.get_willmove_for_merchant(x)
        self.merchants_df['will_move'] = self.merchants_df['erkenningsNummer'].apply(will_move)

        def wants_to_expand(x):
            if x['status'] == "vpl":
                return len(x['plaatsen']) < x['voorkeur.maximum']
            else:
                return None
        self.merchants_df['wants_expand'] = self.merchants_df.apply(wants_to_expand, axis=1)

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
        df_1 = self.merchants_df[(self.merchants_df['attending'] != "no") & (self.merchants_df['status'] == "vpl")]
        df_2 = self.merchants_df[(self.merchants_df['attending'] == "yes") & (self.merchants_df['status'] != "vpl")]
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

    def dequeue_marchant(self, merchant_id):
        self.merchants_df.drop(merchant_id, inplace=True)

    def dequeue_market_stand(self, stand_id):
        self.positions_df.drop(stand_id, inplace=True)

    def num_merchants_in_queue(self):
        return len(self.merchants_df)

    def num_stands_in_queue(self):
        return len(self.positions_df)

    def get_allocation(self):
        """
        Indelen:
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

        Uitbreiden volgens de verordening:
        1. Uitbreiden vindt plaats in genummerde iteraties: in iteratie 2 wordt gekeken of er nog ondernemers zijn die een tweede plaats willen,
           in iteratie 3 komen ondernemers die een derde plaats willen aan bod, enz.
        2. De uitbreidingsfase eindigt indien er geen geschikte marktplaatsen meer zijn, of als elke ondernemer tevreden is.
        3. Voor alle ondernemers wordt nu gecontroleerd of aan hun minimum eis wordt voldaan.
           Als ze niet het minimum aantal plaatsen toegewezen hebben gekregen worden ze afgewezen op deze grond.
        4. Tot slot wordt geprobeerd om tot nu toe niet ingedeelde ondernemers alsnog in te delen.
           Vanwege afwijzingen in de voorgaande stap is er wellicht ruimte vrijgekomen voor andere ondernemers met een lagere sorteringsprioriteit.

           reminder: aLijst, vervangers, plaatsvoorkeur
        """

        market_output = MarketArrangement(market_id=self.market_id, market_date=self.market_date)
        print(self.merchants_df.info())

        print("open plaatsen: ", len(self.positions_df))
        print("ondenemers niet ingedeeld: ", len(self.merchants_df))

        df = self.merchants_df.query("erkenningsNummer == '4000186000'")
        print(df)

        df = self.merchants_df.query("status == 'vpl' & will_move == 'no' & wants_expand == False")
        for index, row in df.iterrows():
            erk = row['erkenningsNummer']
            stands = row['plaatsen']
            market_output.add_allocation(erk, stands, self.merchant_object_by_id(erk))
            try:
                self.dequeue_marchant(erk)
            except KeyError as e:
                print("dubbel ?", erk)
            for st in stands:
                self.dequeue_market_stand(st)

        print("open plaatsen: ", len(self.positions_df))
        print("ondenemers niet ingedeeld: ", len(self.merchants_df))

        return {}
        print("ondenemers (vpl) die niet willen verplaatsen of uitbreiden:")
        print(df)

        df = self.merchants_df.query("status == 'vpl' & will_move == 'yes' & wants_expand == False")
        print("ondenemers (vpl) die WEL willen verplaatsen maar niet uitbreiden:")
        print(df)

        df = self.merchants_df.query("status == 'vpl' & wants_expand == True")
        print("ondenemers (vpl) die WEL willen uitbreiden:")
        print(df)

        print(df[["description", "will_move", "wants_expand", "plaatsen", "voorkeur.maximum", "voorkeur.minimum", "pref"]])
        return {}


if __name__ == "__main__":
    from inputdata import FixtureDataprovider
    dp = FixtureDataprovider("../../fixtures/dapp_20211030/a_input.json")
    a = Allocator(dp)
    a.get_allocation()

