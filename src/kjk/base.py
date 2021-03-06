import pandas as pd
from datetime import date
from kjk.outputdata import MarketArrangement
from kjk.utils import MarketStandClusterFinder, RejectionReasonManager
from kjk.utils import BranchesScrutenizer
from kjk.utils import PreferredStandFinder
from kjk.logging import clog, log
from pandas.core.computation.ops import UndefinedVariableError
from kjk.rejection_reasons import BRANCHE_FULL, MINIMUM_UNAVAILABLE
from kjk.rejection_reasons import VPL_POSITION_NOT_AVAILABLE
from kjk.rejection_reasons import PREF_NOT_AVAILABLE

pd.options.mode.chained_assignment = "raise"

# xls export
XLS_EXPORT = False

# dataframe views for debugging
EXPANDERS_VIEW = [
    "description",
    "voorkeur.maximum",
    "voorkeur.minimum",
    "plaatsen",
    "pref",
    "voorkeur.anywhere",
]
MERCHANTS_SORTED_VIEW = [
    "sollicitatieNummer",
    "pref",
    "voorkeur.branches",
    "voorkeur.minimum",
    "voorkeur.maximum",
]
ALIST_VIEW = ["erkenningsNummer", "description", "alist", "sollicitatieNummer"]
BRANCHE_VIEW = [
    "erkenningsNummer",
    "description",
    "voorkeur.branches",
    "branche_required",
]

STRATEGY_EXP_FULL = 1
STRATEGY_EXP_SOME = 2
STRATEGY_EXP_NONE = 3

MODE_ALIST = "alist == True"
MODE_BLIST = "alist != True"


class VPLCollisionError(Exception):
    """this will be raised if two VPL merchants claim the same market position. (should never happen)"""

    pass


class MerchantNotFoundError(Exception):
    """this will be raised if a merchant id can not be found in the input data. (should never happen)"""

    pass


class MerchantDequeueError(Exception):
    """this will be raised if a merchant id can not be removed from the queue (should never happen)"""

    pass


class NoMerchantsForMarketError(Exception):
    """this will be raised when no merchants are found for the market"""

    pass


class MarketStandDequeueError(Exception):
    """
    this will be when a stand can not be removed from the queue (should never happen)
    Assigning more than one merchant to the same stand id will cause this error.
    """

    pass


EXPANSION_MODE_GREEDY = 1
EXPANSION_MODE_LAZY = 2


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

        self.rejection_reasons = RejectionReasonManager()

        # start with a-listed people
        self.list_mode = MODE_ALIST

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
        self.obstacles = dp.get_obstacles()

        self.blocked_stands = []
        if self.market["kiesJeKraamGeblokkeerdePlaatsen"] is not None:
            self.blocked_stands = self.market["kiesJeKraamGeblokkeerdePlaatsen"].split(
                ","
            )

        # do some bookkeeping
        self.allocations_per_phase = {}
        self.phase_id = "Phase 1"

        # guard the max branch positions
        self.branches_scrutenizer = BranchesScrutenizer(self.branches)

        # market id and date
        self.market_id = dp.get_market_id()
        self.market_date = dp.get_market_date()

        # output object
        self.market_output = MarketArrangement(
            market_id=self.market_id, market_date=self.market_date
        )
        self.market_output.set_config(self.market)
        self.market_output.set_branches(self.branches)
        self.market_output.set_market_positions(self.open_positions)
        self.market_output.set_merchants(self.merchants)
        self.market_output.set_prefs(self.prefs)
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
        self.merchants_df.drop_duplicates(
            subset="erkenningsNummer", keep="first", inplace=True
        )

        # prefs of all soll-merchants sorted by soll_nr and priority
        self.soll_nr_weighted_prefs = []

        # create a dataframe with merchants attending the market
        # and create a positions dataframe
        # these dataframes will be used in the allocation
        self.prepare_merchants()
        self.prepare_stands()
        self.back_up_stand_queue = self.positions_df.copy()
        self.back_up_merchant_queue = self.merchants_df.copy()

        # create a sparse datastructure for branche lookup per stand id
        plaats_ids = self.positions_df["plaatsId"].to_list()
        branches = self.positions_df["branches"].to_list()
        stand_branche_dict = dict(zip(plaats_ids, branches))

        # create a sparse datastructure for evi lookup per stand id
        plaats_ids = self.positions_df["plaatsId"].to_list()
        evis = self.positions_df["verkoopinrichting"].to_list()
        stand_evi_dict = dict(zip(plaats_ids, evis))

        # create a sparse datastructure for bak lookup per stand id
        plaats_ids = self.positions_df["plaatsId"].to_list()
        try:
            baks = self.positions_df["bakType"].to_list()
        except KeyError:
            baks = [None] * len(plaats_ids)
        stand_bak_dict = dict(zip(plaats_ids, baks))

        # created soll_nr weighted prefs
        self.create_sollnr_weighted_prefs()

        self.cluster_finder = MarketStandClusterFinder(
            dp.get_market_blocks(),
            dp.get_obstacles(),
            stand_branche_dict,
            stand_evi_dict,
            stand_bak_dict,
            self.branches,
            weighted_prefs=self.soll_nr_weighted_prefs,
            blocked_stands=self.blocked_stands,
        )

        self.cluster_finder.set_market_info_delegate(self)

        # collection for holding stand ids for evi stands
        self.evi_ids = []
        self.populate_evi_stand_ids()

        # lazy or greedy expansions
        self.expansion_mode = EXPANSION_MODE_LAZY

        self.num_evi_stands = len(self.get_evi_stands())
        self.num_bak_stands = len(self.get_baking_positions())

        # export xls for debugging
        if XLS_EXPORT:
            # save to text for manual debugging
            self.merchants_df.to_markdown("../../merchants.md")
            self.merchants_df.to_excel("../../ondernemers.xls")
            self.positions_df.to_excel("../../kramen.xls")
            self.branches_df.to_excel("../../branches.xls")

    def set_mode_blist(self):
        """set mode to blist, this is used in query format strings"""
        self.list_mode = MODE_BLIST

    def market_has_unused_bak_space(self):
        """
        Check if the market has unused bak space.
        This will allow non bak vpl merchants that want to move
        to get a bak stand.
        """
        df = self.merchants_df.query("has_bak == True")
        return df["voorkeur.maximum"].sum() < self.num_bak_stands

    def market_has_unused_evi_space(self):
        """
        Check if the market has unused evi space.
        This will allow non evi vpl merchants that want to move
        to get an evi stand.
        """
        df = self.merchants_df.query("has_evi == 'yes'")
        return df["voorkeur.maximum"].sum() < self.num_evi_stands

    def market_has_unused_branche_space(self, branches):
        """
        Check if the market has unused branche space.
        This will allow non branche vpl merchants that want to move
        to get a branched stand.
        """
        for branche in branches:

            def has_branch(x):
                try:
                    if branche in x:
                        return True
                except TypeError:
                    # nobranches == nan in dataframe
                    pass
                return False

            try:
                if len(self.merchants_df) < 1:
                    return True
                has_br = self.merchants_df["voorkeur.branches"].apply(has_branch)
                demand_for_branche = self.merchants_df[has_br]["voorkeur.maximum"].sum()
                stands = self.get_stand_for_branche(branche)
                stands_available_for_branche = len(stands)
                if stands_available_for_branche <= demand_for_branche:
                    return False
            except KeyError:
                return False
        return True

    def get_debug_data(self):
        """helper to track in which phase a merchant is allocated"""
        return self.allocations_per_phase

    def set_allocation_phase(self, phase_id):
        """set current allocation phase, used in logging"""
        self.phase_id = phase_id

    def set_expansion_mode(self, mode):
        """
        set expansion mode:
        'EXPANSION_MODE_GREEDY' will allocate minimum stands in first pass
        (not market-regulation compatible)
        """
        self.expansion_mode = mode

    def _prepare_expansion(
        self, erk, stands, size, merchant_branches, bak, evi, bak_type
    ):
        """
        If a merchant wants to expand, the stands can not be assigned right away.
        We 'reserve' the stands suited for expansion by trying to avoid them later in
        allocation process. This increases the changes for expansion.
        """
        if len(stands) == 0:
            return
        expansion_candidates = self.cluster_finder.find_valid_expansion(
            stands,
            total_size=size,
            merchant_branche=merchant_branches,
            bak_merchant=bak,
            evi_merchant=evi,
            ignore_check_available=stands,
            bak_type=bak_type,
        )
        clog.debug(
            f"PREPARE EXPANSION {erk} stands: {stands} expansion_candidates: {expansion_candidates}",
        )
        for exp in expansion_candidates:
            self.cluster_finder.set_stands_reserved(exp, erk=erk)
        clog.debug(
            f"RESERVED STANDS {self.cluster_finder.stands_reserved_for_expansion}"
        )
        if (
            len(expansion_candidates) > 0
            and self.expansion_mode == EXPANSION_MODE_GREEDY
        ):
            self._allocate_stands_to_merchant(
                expansion_candidates[0], erk, dequeue_merchant=False
            )

    def create_merchant_dict(self):
        """create a sparse datastructure for merchant lookup, by 'erkenningsnummer'"""
        d = {}
        for m in self.merchants:
            d[m["erkenningsNummer"]] = m
        return d

    def merchant_object_by_id(self, merchant_id):
        """merchant lookup"""
        try:
            return self.merchants_dict[merchant_id]
        except KeyError:
            raise MerchantNotFoundError(f"mechant not found: {merchant_id}")

    def add_has_stands(self):
        """add has_stands boolean to the merchant dataframe,
        exp merchants may or may not have stands"""

        def has_stands(x):
            try:
                if len(x["plaatsen"]) > 0:
                    return True
                return False
            except Exception:
                clog.warning("No valid plaatsen field for merchant assume []")
                return False

        self.merchants_df["has_stands"] = self.merchants_df.apply(has_stands, axis=1)

    def add_bak_type(self):
        """add bak_type to the merchant dataframe
        make sure there is a value so we don't have data quality issues later on."""

        def bak_type(x):
            try:
                return x["voorkeur.bakType"]
            except Exception:
                return "geen"

        self.merchants_df["bak_type"] = self.merchants_df.apply(bak_type, axis=1)

    def add_has_bak(self):
        def has_bak(x):
            try:
                if x["voorkeur.bakType"] == "bak":
                    return True
                return False
            except Exception:
                clog.warning("No valid branches field for merchant assume []")
                return False

        self.merchants_df["has_bak"] = self.merchants_df.apply(has_bak, axis=1)

    def create_expanders_set(self):
        """
        Add boolean column to the merchants dataframe
        for people who want to expand.
        And create a separate dataframe with the expanders.
        Soll merchants get 1 stand as default.
        Vpl and equivalent will get their fixed positions and want to expand
        if max (or min) is larger than len(fixed)
        """

        def wants_to_expand(x):
            if x["status"] in ("vpl", "tvpl", "exp", "expf", "eb"):
                try:
                    return int(x["voorkeur.maximum"]) > len(x["plaatsen"])
                except KeyError:
                    return False
                except ValueError:
                    return False
            else:
                try:
                    return int(x["voorkeur.maximum"]) > 1
                except KeyError:
                    return False
                except ValueError:
                    return False

        self.merchants_df["wants_expand"] = self.merchants_df.apply(
            wants_to_expand, axis=1
        )
        self.expanders_df = self.merchants_df.query("wants_expand == True").copy()

    def _add_vpl_moved_status_to_expanders(self, movers_dict):
        """
        If two vpl's compete for the same expansion spot.
        The vpl that did not move should get the stand.
        """

        def did_succesfully_expand(x):
            erk = x["erkenningsNummer"]
            if erk in movers_dict:
                return True
            return False

        if self.expanders_df is not None:
            if len(self.expanders_df) > 0:
                self.expanders_df["vpl_did_move"] = self.expanders_df.apply(
                    did_succesfully_expand, axis=1
                )
            else:
                self.expanders_df["vpl_did_move"] = False

    def create_reducers_set(self):
        """
        vpl merchants can opt to have less stands than their fixed positions.
        Add a boolean column to the merchants dataframe.
        """

        def wants_to_reduce(x):
            if x["status"] in ("vpl", "tvpl", "exp", "expf", "eb"):
                try:
                    return int(x["voorkeur.maximum"]) < len(x["plaatsen"])
                except KeyError:
                    return False
                except ValueError:
                    return False
            else:
                return False

        self.merchants_df["wants_reduce"] = self.merchants_df.apply(
            wants_to_reduce, axis=1
        )

        def reduce_stands(x):
            erk = ""
            try:
                if x["wants_reduce"]:
                    erk = x["erkenningsNummer"]
                    x["plaatsen"] = x["plaatsen"][: x["voorkeur.maximum"]]
            except Exception:
                clog.warning(f"Verminderen stand vpl {erk} mislukt!")
                pass
            return x

        self.merchants_df = self.merchants_df.apply(reduce_stands, axis=1)

    def prepare_merchants(self):
        """prepare the merchants list for allocation"""
        self.df_for_attending_merchants()
        if len(self.merchants_df) == 0:
            raise NoMerchantsForMarketError(
                "Geen ondernemers aangemeld voor deze markt"
            )
        self.add_mandatory_columns()
        self.add_prefs_for_merchant()
        self.add_alist_status_for_merchant()
        self.add_required_branche_for_merchant()
        self.add_evi_for_merchant()
        self.add_has_stands()
        self.add_has_bak()
        self.add_bak_type()
        self.create_expanders_set()
        self.create_reducers_set()
        self.merchants_df.set_index("erkenningsNummer", inplace=True)
        self.merchants_df["erkenningsNummer"] = self.merchants_df.index
        self.merchants_df["sollicitatieNummer"] = pd.to_numeric(
            self.merchants_df["sollicitatieNummer"]
        )
        self.merchants_df["voorkeur.minimum"] = self.merchants_df[
            "voorkeur.minimum"
        ].fillna(1.0)

    def prepare_stands(self):
        """prepare the stands list for allocation"""

        def required(x):
            try:
                return self.get_required_for_branche(x)
            except KeyError:
                return "unknown"

        is_required = self.positions_df["branches"].apply(required)
        self.positions_df["required"] = is_required
        self.positions_df.set_index("plaatsId", inplace=True)
        self.positions_df["plaatsId"] = self.positions_df.index

        def clean_branches(x):
            if isinstance(x, list):
                return x
            return []

        cleansed_branches = self.positions_df["branches"].apply(clean_branches)
        self.positions_df["branches"] = cleansed_branches

        try:

            def is_inactive(x):
                if x == True:
                    return False
                return True

            active = self.positions_df["inactive"].apply(is_inactive)
            self.positions_df = self.positions_df[active]
        except KeyError:
            # No inactive stand found in cofiguration
            pass

    def get_required_for_branche(self, b):
        """
        Add a required column to the branches dataframe
        """
        try:
            if len(b) == 0:
                return "no"
        except TypeError:
            return "no"
        # assumption:
        # if more than one branche per stand always means bak?
        if len(b) >= 1:
            result = self.branches_df[self.branches_df["brancheId"] == b[0]]
            if len(result) > 0 and result.iloc[0]["verplicht"] == True:
                return "yes"
            else:
                return "no"
        return "unknown"

    def get_prefs_for_merchant(self, merchant_number):
        """get position pref for merchant_number (erkenningsNummer)"""
        result_df = self.prefs_df[
            self.prefs_df["erkenningsNummer"] == merchant_number
        ].copy()
        result_df.sort_values(by=["priority"], inplace=True)
        plaats = result_df["plaatsId"].to_list()
        return plaats

    def get_willmove_for_merchant(self, merchant_number):
        """check if this merchant wants to move (only relevant for vpl) . merchant_number (erkenningsNummer)"""
        result_df = self.prefs_df[self.prefs_df["erkenningsNummer"] == merchant_number]
        plaats = result_df["plaatsId"].to_list()
        if len(plaats) > 0:
            return "yes"
        else:
            return "no"

    def add_alist_status_for_merchant(self):
        """
        Add an A-list boolean to the merchants dataframe.
        If true a merchant will allocated bofore others (B-list)
        """

        def prefs(x):
            try:
                result_df = self.a_list_df[
                    self.a_list_df["erkenningsNummer"] == x
                ].copy()
                return len(result_df) > 0
            except KeyError:
                return False

        self.merchants_df["alist"] = self.merchants_df["erkenningsNummer"].apply(prefs)

    def add_mandatory_columns(self):
        """
        Add missing columns with no data at all
        """
        # This script should be a drop in replacement for the TypeScript KjK
        # allocations. We have to deal with bad data quality.
        # For some markets on ACC (and maybe PROD) there is no 'voorkeur'
        # for any merchant. Let's make stuff up.
        for c in [
            ("voorkeur.branches", []),
            ("voorkeur.verkoopinrichting", []),
            ("voorkeur.minimum", 1),
            ("voorkeur.maximum", 1),
        ]:
            try:
                self.merchants_df[c[0]]
            except KeyError:
                self.merchants_df[c[0]] = [c[1] for x in range(len(self.merchants_df))]

    def add_required_branche_for_merchant(self):
        """
        Does the merchant sell a required branche?
        If true this merchant will only be allocated on 'branched' stands.
        """

        def required(x):
            try:
                return self.get_required_for_branche(x)
            except KeyError:
                return "unknown"

        is_required = self.merchants_df["voorkeur.branches"].apply(required)
        self.merchants_df["branche_required"] = is_required

        def clean_branches(x):
            if isinstance(x, list):
                return x
            return []

        cleansed_branches = self.merchants_df["voorkeur.branches"].apply(clean_branches)
        self.merchants_df["voorkeur.branches"] = cleansed_branches

    def add_evi_for_merchant(self):
        """
        Does the merchant bring his own stand inventory.
        """

        def has_evi(x):
            try:
                if "eigen-materieel" in x:
                    return "yes"
                else:
                    return "no"
            except TypeError:
                return "unknown"

        hasevi = self.merchants_df["voorkeur.verkoopinrichting"].apply(has_evi)
        self.merchants_df["has_evi"] = hasevi

    def create_sollnr_weighted_prefs(self):
        """
        Create a list of stand numbers sorted on pref-prio and soll nr.
        So that the stand with the lowest prio of the merchant with the highest
        soll nr will be given away first (first elem in the list). The stand with the highest prio of the merchant with the
        lowest soll nr will be given away last. (last elem in the list)
        """
        p = {}

        def weighted_prefs(merch):
            soll_nr = merch["sollicitatieNummer"]
            pref = merch["pref"]
            erk = merch["erkenningsNummer"]
            if len(pref) > 0:
                p[soll_nr] = self.get_prefs_for_merchant(erk)

        self.merchants_df[["erkenningsNummer", "sollicitatieNummer", "pref"]].apply(
            weighted_prefs, axis=1
        )
        _prefs = []
        for m in sorted(p.items()):
            for std in m[1]:
                if std not in _prefs:
                    _prefs.append(std)
        _prefs.reverse()
        self.soll_nr_weighted_prefs = _prefs

    def add_prefs_for_merchant(self):
        """add position preferences to the merchant dataframe"""

        def prefs(x):
            try:
                merchant_prefs = self.get_prefs_for_merchant(x)
                return merchant_prefs
            except KeyError:
                return []

        self.merchants_df["pref"] = self.merchants_df["erkenningsNummer"].apply(prefs)

        def will_move(x):
            try:
                return self.get_willmove_for_merchant(x)
            except KeyError:
                return "no"

        self.merchants_df["will_move"] = self.merchants_df["erkenningsNummer"].apply(
            will_move
        )

    def df_for_attending_merchants(self):
        """
        Wich merchants are actually attending the market?
        - vpl, tvpl and eb only have to tell when they are NOT attending
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
            except KeyError:
                return "na"

        self.merchants_df["attending"] = self.merchants_df["erkenningsNummer"].apply(
            is_attending_market
        )
        df_1 = self.merchants_df.query(
            "attending != 'no' & (status == 'vpl' | status == 'tvpl' | status == 'eb')"
        )
        df_2 = self.merchants_df.query(
            "attending == 'yes' & (status != 'vpl' & status != 'tvpl' & status != 'eb')"
        )
        self.merchants_df = pd.concat([df_1, df_2])

        def check_absent(x):
            try:
                if x["voorkeur.absentUntil"] != None and x["voorkeur.absentFrom"]:
                    from_str = x["voorkeur.absentFrom"]
                    from_date = date.fromisoformat(from_str)
                    until_str = x["voorkeur.absentUntil"]
                    until_date = date.fromisoformat(until_str)
                    if from_date <= self.market_date <= until_date:
                        return False
                return True
            except TypeError:
                return True

        try:
            df = self.merchants_df[
                ["voorkeur.absentFrom", "voorkeur.absentUntil"]
            ].apply(check_absent, axis=1)
            self.merchants_df = self.merchants_df[df]
        except KeyError:
            clog.warning("No merchants records found for preriodic absence.")

    def get_vpl_for_position(self, position):
        """return a merchant number for a fixed position, reurn None is no merchant found"""

        def num_positions(x):
            if position in x:
                return True
            return False

        has_positions = self.merchants_df["plaatsen"].apply(num_positions)
        result_df = self.merchants_df[has_positions]
        if len(result_df) == 1:
            return result_df.iloc[0]["erkenningsNummer"]
        if len(result_df) > 1:
            raise VPLCollisionError(
                f"more than one vpl merchant for position {position}"
            )
        return None

    def get_merchant_for_branche(self, branche, status=None):
        """get all merchants for a given branche for this market"""

        def has_branch(x):
            try:
                if branche in x:
                    return True
            except TypeError:
                # nobranches == nan in dataframe
                pass
            return False

        has_branch = self.merchants_df["voorkeur.branches"].apply(has_branch)
        result_df = self.merchants_df[has_branch][["erkenningsNummer", "status"]]
        if status is not None:
            result_df = result_df[result_df["status"] == status]
        result_df = result_df["erkenningsNummer"]
        return result_df.to_list()

    def get_baking_positions(self):
        """get all baking positions for this market"""

        def has_bak(x):
            if "bak" == x:
                return True
            return False

        try:
            has_bak_df = self.positions_df["bakType"].apply(has_bak)
            result_df = self.positions_df[has_bak_df]["plaatsId"]
            return result_df.to_list()
        except KeyError:
            return []

    def get_rsvp_for_merchant(self, merchant_number):
        """boolean, Is this mechant attending this market?"""
        result_df = self.rsvp_df[self.rsvp_df["erkenningsNummer"] == merchant_number]
        if len(result_df) == 1:
            return result_df.iloc[0]["attending"]
        return None

    def populate_evi_stand_ids(self):
        """populate the evi stand ids collection"""
        for i, p in self.positions_df.iterrows():
            try:
                if "eigen-materieel" in p["verkoopinrichting"]:
                    self.evi_ids.append(p["plaatsId"])
            except TypeError:
                pass  # we have nan values in this column, asume no evi

    def get_evi_stands(self):
        """return a dataframe with evi stands"""

        def has_evi(x):
            try:
                if "eigen-materieel" in x:
                    return True
            except TypeError:
                pass  # nan is False (no evi)
            return False

        hasevi = self.positions_df["verkoopinrichting"].apply(has_evi)
        return self.positions_df[hasevi]

    def get_merchants_with_evi(self, status=None):
        """return list of merchant numbers with evi, optionally filtered by status ('soll', 'vpl', etc)"""

        def has_evi(x):
            try:
                if "eigen-materieel" in x:
                    return True
            except TypeError:
                # nobranches == nan in dataframe
                pass
            return False

        has_evi = self.merchants_df["voorkeur.verkoopinrichting"].apply(has_evi)
        result_df = self.merchants_df[has_evi][["erkenningsNummer", "status"]]
        if status is not None:
            result_df = result_df[result_df["status"] == status]
        result_df = result_df["erkenningsNummer"]
        return result_df.to_list()

    def dequeue_merchant(self, merchant_id):
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
        return stand["branches"].iloc[0]

    def get_stand_for_branche(self, branche):
        """
        Get the stands data-slice for given branche.
        """

        def is_branche(x):
            try:
                if branche in x:
                    return True
            except TypeError:
                pass  # asume nan is False (no branche)
            return False

        stands = self.positions_df["branches"].apply(is_branche)
        return self.positions_df[stands]

    def reject_remaining_merchants(self):
        """
        If the market is full, reject the merchants still in the queue.
        """
        log.warning(
            "Ondernemers af te wijzen in deze fase: {}".format(len(self.merchants_df))
        )
        for index, row in self.merchants_df.iterrows():
            erk = row["erkenningsNummer"]
            reason = self.rejection_reasons.get_rejection_reason_for_merchant(erk)
            self._reject_merchant(erk, reason)

    def _reject_merchant(self, erk, reason):
        """
        Reject a merchant, and dequeue.
        """
        self.market_output.add_rejection(erk, reason, self.merchant_object_by_id(erk))
        try:
            self.dequeue_merchant(erk)
        except KeyError:
            raise MerchantDequeueError(
                "Could not dequeue merchant, there may be a duplicate merchant id in the input data!"
            )

    def _allocation_wanted(self, erk, stands_to_alloc):
        """
        Does the soll merchant want the assigned stand?
        If anywhere is false he only wants his preferred stands.
        """
        try:
            df = self.merchants_df.query(
                "`voorkeur.anywhere` == False & status == 'soll'"
            )
            if erk not in df["erkenningsNummer"].to_list():
                return True
        except UndefinedVariableError:  # pandas error not all tests have 'anywhere'
            return True
        # if anywhere is off all stands should be in prefs
        prefs = self.get_prefs_for_merchant(erk)
        if len(prefs) == 0:
            return True
        return all([std in prefs for std in stands_to_alloc])

    def _allocation_allowed(self, merchant_obj, branches):
        """
        Allocation is allowed if max branches is not exceeded.
        vpl, eb always gets the stand, even if max branche is exeeded
        """
        if "vpl" in merchant_obj["status"]:
            return True
        if "eb" in merchant_obj["status"]:
            return True
        return self.branches_scrutenizer.allocation_allowed(branches)

    def _allocate_stands_to_merchant(self, stands_to_alloc, erk, dequeue_merchant=True):
        clog.debug(
            f"ALLOCATE STAND TO MERCHANT {erk} fase: {self.phase_id} stands: {stands_to_alloc}"
        )
        if len(stands_to_alloc) > 0:
            merchant_obj = self.merchant_object_by_id(erk)

            # We have some data quality issues
            # each merchant should spec his merch
            # in KjK, see exception handling
            allocation_allowed = True  # unless the scrutenizer tells otherwise
            branches = []
            m_id = self.market_id
            m_date = self.market_date

            merchant_dequeue_error = False
            stand_dequeue_error = False
            allocation_wanted = self._allocation_wanted(erk, stands_to_alloc)
            try:
                bakType = merchant_obj["voorkeur"]["bakType"]
            except KeyError:
                bakType = None
            try:
                branches = merchant_obj["voorkeur"]["branches"]
            except KeyError:
                clog.error(
                    f"ondernemer {erk} heeft geen branche in zijn voorkeur, markt {m_id} op {m_date}"
                )
            except IndexError:
                clog.error(
                    f"ondernemer {erk} heeft geen branche in zijn voorkeur, markt {m_id} op {m_date}"
                )

            allocation_allowed = self._allocation_allowed(
                merchant_obj, branches + [bakType]
            )
            if not allocation_allowed:
                self.rejection_reasons.add_rejection_reason_for_merchant(
                    erk, BRANCHE_FULL
                )

            if allocation_allowed and allocation_wanted:
                # some times we need to know the phase in wich a merchant is allocated
                # mostly for debugging but we may decide to report this to market-dep
                if self.phase_id not in self.allocations_per_phase:
                    self.allocations_per_phase[self.phase_id] = []
                self.allocations_per_phase[self.phase_id].append(
                    {"erk": erk, "stands": stands_to_alloc}
                )
                for st in stands_to_alloc:
                    try:
                        self.dequeue_market_stand(st)
                    except KeyError:
                        clog.debug(f"STAND DEQUEUE ERROR {st}")
                        stand_dequeue_error = True
                try:
                    if dequeue_merchant:
                        self.dequeue_merchant(erk)
                except KeyError:
                    stand_dequeue_error = True

                if stand_dequeue_error:
                    raise MarketStandDequeueError(f"Allocation error: {erk} - {st}")
                if merchant_dequeue_error:
                    raise MerchantDequeueError(
                        "Could not dequeue merchant, there may be a duplicate merchant id in the input data!"
                    )

                # max 'bak' is specified in the branches section
                # so append bak (or bak-licht) to the allocated branches
                if bakType is not None and bakType != "geen":
                    branches = branches.copy()
                    branches.append(bakType)

                self.branches_scrutenizer.add_allocation(branches, stands_to_alloc)
                self.cluster_finder.set_stands_allocated(stands_to_alloc)
                self.market_output.add_allocation(erk, stands_to_alloc, merchant_obj)

    def _allocate_solls_for_query(
        self, query, print_df=False, check_branche_bak_evi=True
    ):
        if query == "all":
            result_list = self.merchants_df.copy()
        else:
            result_list = self.merchants_df.query(query)

        if print_df:
            print(result_list)
            # print(self.cluster_finder.stands_allocated)

        if result_list is None:
            return

        log.info("Ondernemers te alloceren in deze fase: {}".format(len(result_list)))
        for _, row in result_list.iterrows():

            erk = row["erkenningsNummer"]
            clog.debug(f"TRYING TO ALLOCATE SOLLICITANT {erk} phase: {self.phase_id}")

            pref = row["pref"]
            minimal = row["voorkeur.minimum"]
            maximal = row["voorkeur.maximum"]
            expand = row["wants_expand"]
            merchant_branches = row["voorkeur.branches"]
            evi = row["has_evi"] == "yes"
            bak = row["has_bak"]
            bak_type = row["bak_type"]
            anywhere = row.get("voorkeur.anywhere", False)

            minimal_possible = self.cluster_finder.find_valid_cluster(
                pref,
                int(minimal),
                merchant_branche=merchant_branches,
                bak_merchant=bak,
                evi_merchant=evi,
                anywhere=anywhere,
                check_branche_bak_evi=check_branche_bak_evi,
                erk=erk,
                bak_type=bak_type,
            )
            if len(minimal_possible) == 0:
                # do not reject yet, this merchant should be able to compete
                # for reclaimed stands in a later phase
                if not anywhere and len(pref) > 0:
                    self.rejection_reasons.add_rejection_reason_for_merchant(
                        erk, PREF_NOT_AVAILABLE
                    )
                else:
                    self.rejection_reasons.add_rejection_reason_for_merchant(
                        erk, MINIMUM_UNAVAILABLE
                    )
                continue
            elif row["status"] == "tvplz":
                # this is the exception for tvplz merchants
                # they do not have stands but have the right to
                # a minimal number of stands, so if possible allocate right
                # now.
                self._allocate_stands_to_merchant(minimal_possible, erk)
                continue

            stds = []
            # 1. first try to find cluster for the maximum wanted number of stands
            if len(stds) == 0:
                stds = self.cluster_finder.find_valid_cluster(
                    pref,
                    size=int(maximal),
                    merchant_branche=merchant_branches,
                    bak_merchant=bak,
                    evi_merchant=evi,
                    anywhere=anywhere,
                    check_branche_bak_evi=check_branche_bak_evi,
                    erk=erk,
                    bak_type=bak_type,
                )

            clog.debug(
                f"ALLOCATE SOLLICITANT {erk} minimal {minimal} maximal {maximal} pref {pref} minimal_possible {minimal_possible} stds {stds}"
            )

            # 2. then try to find cluster for the minimum wanted number of stands
            if len(stds) == 0 and len(minimal_possible) > 0:
                stds = minimal_possible

            if len(stds) > 1 and query != "all":
                # TODO: find the sweetspot inside this cluster
                psf = PreferredStandFinder(stds, pref)
                stds = psf.produce()

            if expand:
                self._prepare_expansion(
                    erk,
                    stds,
                    int(row["voorkeur.maximum"]),
                    merchant_branches,
                    bak,
                    evi,
                    bak_type,
                )

            self._allocate_stands_to_merchant(stds, erk)

    def _expand_for_merchants(self, df):
        for _, row in df.iterrows():
            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            merchant_branches = row["voorkeur.branches"]
            bak = row["has_bak"]
            evi = row["has_evi"] == "yes"
            maxi = row["voorkeur.maximum"]
            status = row["status"]
            bak_type = row["bak_type"]
            expansion_prefs = None
            anywhere = None
            if status == "eb":
                expansion_prefs = row["pref"]
                anywhere = row.get("voorkeur.anywhere", True)

            # exp, expf can not expand
            if status in ("exp", "expf"):
                continue

            assigned_stands = self.market_output.get_assigned_stands_for_merchant(erk)
            if assigned_stands is not None:
                if len(assigned_stands) >= maxi:
                    continue
                stands = self.cluster_finder.find_valid_expansion(
                    fixed_positions=assigned_stands,
                    total_size=len(assigned_stands) + 1,
                    merchant_branche=merchant_branches,
                    bak_merchant=bak,
                    evi_merchant=evi,
                    ignore_check_available=assigned_stands,
                    erk=erk,
                    bak_type=bak_type,
                    allocate=True,
                    prefs=expansion_prefs,
                    anywhere=anywhere,
                    status=status,
                )
                clog.debug(
                    f"EXPAND FOR MERCHANTS {erk} status {status} assigned {assigned_stands} anywhere {anywhere} prefs {expansion_prefs} stands {stands}"
                )
                if len(stands) > 0:
                    self._allocate_stands_to_merchant(
                        stands[0], erk, dequeue_merchant=False
                    )

    def _allocate_vpl_for_query(self, query, print_df=False):
        df = self.merchants_df.query(query)
        if df is None:
            return
        if print_df:
            print(df)
        for _, row in df.iterrows():
            erk = row["erkenningsNummer"]
            try:
                stands = row["plaatsen"]
                expand = row["wants_expand"]
                merchant_branches = row["voorkeur.branches"]
                evi = row["has_evi"] == "yes"
                bak = row["has_bak"]
                bak_type = row["bak_type"]
                if expand:
                    self._prepare_expansion(
                        erk,
                        stands,
                        int(row["voorkeur.maximum"]),
                        merchant_branches,
                        bak,
                        evi,
                        bak_type,
                    )
                self._allocate_stands_to_merchant(stands, erk)
            except MarketStandDequeueError:
                try:
                    self._reject_merchant(erk, VPL_POSITION_NOT_AVAILABLE)
                except MerchantDequeueError:
                    clog.error(
                        f"VPL plaatsen niet beschikbaar voor erkenningsNummer {erk}"
                    )
