from kjk.utils import TradePlacesSolver
from kjk.base import MarketStandDequeueError
from kjk.base import MerchantDequeueError
from kjk.rejection_reasons import VPL_POSITION_NOT_AVAILABLE
from kjk.logging import clog
from kjk.base import BaseAllocator


class MovingVPLSolver:
    """
    VPL and TVPL merchants can choose to move to another location on the market
    This adds complexity to the allocation:
        1. They can not move to a 'branche-bak-evi' incompatible stands.
        2. They can not move to the fixed position of other vpls.
        3. Non 'branche-bak-evi' can only move to 'branche-bak-evi' stand if not required by the market demand.
        4. They should be able to switch/trade places.
        5. Places they leave behind should become available for other movers and merchants.

    This allocator 'friend' class solves this problem.
    """

    def __init__(self, allocator: BaseAllocator, query: str):
        """
        example query: "(status == 'vpl' | status == 'tvpl') & will_move == 'yes'"
        """
        self.allocator = allocator
        self.query = query
        self.df = None
        self.has_conflicts = False
        self.successful_movers = {}

    def execute(self, print_df=False):
        # set the state of the cluster finder
        # to check the availability of branche bak evi
        self.allocator.cluster_finder.set_check_branche_bak_evi(True)

        # get all the vpls who want to move
        df = self.allocator.merchants_df.query(self.query)
        if df is None:
            return
        if print_df:
            print(df)
        self.df = df.copy()

        # bak_type : ('bak', 'bak-licht', 'geen') happens to be alphabetically
        # this simplifies sorting
        self.df.sort_values(
            by=["bak_type", "sollicitatieNummer"], inplace=True, ascending=True
        )

        # STEP 1:
        # first allocate the vpl's that can not move to avoid conflicts
        self._alloc_can_not_move()

        # STEP 2:
        # try to allocate the rest now
        # places from step 1 have become available
        self.fixed_set = None
        while self.vpl_movers_remaining():

            # refresh the data set
            df = self.allocator.merchants_df.query(self.query)
            if df is None:
                return
            self.df = df.copy()
            self.df.sort_values(
                by=["bak_type", "sollicitatieNummer"], inplace=True, ascending=True
            )

            d = self._compute_fixed_wanted()
            merch_dict = d["merch_dict"]
            fixed = d["fixed"]
            wanted = d["wanted"]

            # if A wants to go from 1 to 2 and B wants to go from 2 to 1
            self._allocate_stand_swappers(merch_dict)

            # if two merchants want to move to the same spot
            # we have a conflict
            self.has_conflicts = len(set(wanted)) < len(wanted)

            # if the free postions list does
            # not change anymore we are out of 'save moves'
            # time to solve the conflicts if we can
            # NOTE: this will be the last iteration of this while loop
            if fixed == self.fixed_set:
                self._finalize()
                break
            else:
                # now allocate the vpl's that can move savely
                # meaning that the wanted positions do not intefere with
                # other fixed positions
                self._save_allocate(fixed)

            self.fixed_set = fixed

        # set the state of he cluster finder back to 'normal'
        self.allocator.cluster_finder.set_check_branche_bak_evi(False)

    def vpl_movers_remaining(self):
        df = self.allocator.merchants_df.query(self.query)
        if df is None:
            return
        df = df.copy()
        return len(df) > 0

    def _alloc_can_not_move(self):
        failed = {}
        if self.df is None:
            return
        for _, row in self.df.iterrows():

            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            bak = row["has_bak"]
            evi = row["has_evi"] == "yes"
            bak_type = row["bak_type"]

            # some merchants have their own fixed stands as pref
            # don't ask me why we deal with this by checking overlap
            ignore_pref = any([x in stands for x in pref])

            valid_pref_stands = self.allocator.cluster_finder.find_valid_cluster(
                pref,
                size=len(stands),
                merchant_branche=merchant_branches,
                bak_merchant=bak,
                evi_merchant=evi,
                anywhere=False,
            )
            if len(valid_pref_stands) == 0 or ignore_pref:
                failed[erk] = (stands, row)

        for f in failed.keys():
            erk = f
            stands = stands_to_alloc = failed[f][0]
            row = failed[f][1]
            expand = row["wants_expand"]
            if expand:
                self.allocator._prepare_expansion(
                    erk,
                    stands,
                    int(row["voorkeur.maximum"]),
                    merchant_branches,
                    bak,
                    evi,
                    bak_type,
                )
            try:
                self.allocator._allocate_stands_to_merchant(stands_to_alloc, erk)
            except MarketStandDequeueError:
                try:
                    self.allocator._reject_merchant(erk, VPL_POSITION_NOT_AVAILABLE)
                except MerchantDequeueError:
                    clog.error(
                        f"VPL plaatsen niet beschikbaar voor erkenningsNummer {erk}"
                    )

    def _compute_fixed_wanted(self):
        if self.df is None:
            return {"fixed": [], "wanted": [], "merch_dict": {}}
        fixed = []
        wanted = []
        merch_dict = {}
        for _, row in self.df.iterrows():
            stands = row["plaatsen"]
            fixed += stands
            wanted += row["pref"]
            merch_dict[row["erkenningsNummer"]] = {
                "fixed": stands,
                "wanted": row["pref"],
            }
        return {"fixed": fixed, "wanted": wanted, "merch_dict": merch_dict}

    def _allocate_stand_swappers(self, merch_dict):
        res = TradePlacesSolver(merch_dict).get_position_traders()
        for erk in res:
            traded_stands = merch_dict[erk]["wanted"]
            self.allocator._allocate_stands_to_merchant(traded_stands, erk)

    def _save_allocate(self, fixed):
        if self.df is None:
            return
        for _, row in self.df.iterrows():

            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            bak = row["has_bak"]
            evi = row["has_evi"] == "yes"
            bak_type = row["bak_type"]

            valid_pref_stands = self.allocator.cluster_finder.find_valid_cluster(
                pref,
                size=len(stands),
                merchant_branche=merchant_branches,
                bak_merchant=bak,
                evi_merchant=evi,
                anywhere=False,
            )
            fixed_set = set(fixed)

            intersection = list(fixed_set.intersection(valid_pref_stands))
            own_stands = all(elem in stands for elem in intersection)
            unsave_move = len(intersection) > 0 and own_stands == False

            # do not allocate if wants to move to fixed pos of others
            if unsave_move:
                continue

            if len(valid_pref_stands) < len(stands):
                stands_to_alloc = []
            else:
                stands_to_alloc = valid_pref_stands

            try:
                expand = row["wants_expand"]
                if expand:
                    self.successful_movers[erk] = stands_to_alloc
                    self.allocator._prepare_expansion(
                        erk,
                        stands_to_alloc,
                        int(row["voorkeur.maximum"]),
                        merchant_branches,
                        bak,
                        evi,
                        bak_type,
                    )
                self.allocator._allocate_stands_to_merchant(stands_to_alloc, erk)
            except Exception:
                clog.error(
                    f"VPL plaatsen (verplaatsing) niet beschikbaar voor erkenningsNummer {erk}"
                )

    def get_successful_movers(self):
        return self.successful_movers

    def _finalize(self):
        # first check if we have rejections
        if self.df is None:
            return
        has_rejections = False
        for _, row in self.df.iterrows():
            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            bak = row["has_bak"]
            evi = row["has_evi"] == "yes"
            valid_pref_stands = self.allocator.cluster_finder.find_valid_cluster(
                pref,
                size=len(stands),
                merchant_branche=merchant_branches,
                bak_merchant=bak,
                evi_merchant=evi,
                anywhere=False,
            )
            if len(valid_pref_stands) == 0:
                has_rejections = True
                break

        for _, row in self.df.iterrows():
            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            bak = row["has_bak"]
            evi = row["has_evi"] == "yes"
            expand = row["wants_expand"]
            bak_type = row["bak_type"]
            valid_pref_stands = self.allocator.cluster_finder.find_valid_cluster(
                pref,
                size=len(stands),
                merchant_branche=merchant_branches,
                bak_merchant=bak,
                evi_merchant=evi,
            )

            if self.has_conflicts or has_rejections:
                if expand:
                    self.allocator._prepare_expansion(
                        erk,
                        stands,
                        int(row["voorkeur.maximum"]),
                        merchant_branches,
                        bak,
                        evi,
                        bak_type,
                    )
                # unable to solve conflict stay on fixed positions
                try:
                    self.allocator._allocate_stands_to_merchant(stands, erk)
                except MarketStandDequeueError:
                    try:
                        self.allocator._reject_merchant(erk, VPL_POSITION_NOT_AVAILABLE)
                    except MerchantDequeueError:
                        clog.error(
                            f"VPL plaatsen niet beschikbaar voor erkenningsNummer {erk}"
                        )
            else:
                if expand:
                    self.successful_movers[erk] = valid_pref_stands
                    self.allocator._prepare_expansion(
                        erk,
                        valid_pref_stands,
                        int(row["voorkeur.maximum"]),
                        merchant_branches,
                        bak,
                        evi,
                        bak_type,
                    )
                # no conflicts savely switch positions
                self.allocator._allocate_stands_to_merchant(valid_pref_stands, erk)
