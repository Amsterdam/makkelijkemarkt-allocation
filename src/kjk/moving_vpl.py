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

    def vpl_movers_remaining(self):
        df = self.allocator.merchants_df.query(self.query)
        if df is None:
            return
        df = df.copy()
        return len(df) > 0

    def execute(self, print_df=False):
        self.allocator.cluster_finder.set_check_branche_bak_evi(True)

        df = self.allocator.merchants_df.query(self.query)
        if df is None:
            return
        if print_df:
            print(df)
        df = df.copy()
        df.sort_values(by=["sollicitatieNummer"], inplace=True, ascending=True)

        # STEP 1:
        # first allocate the vpl's that can not move to avoid conflicts
        failed = {}
        for _, row in df.iterrows():

            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            bak = row["has_bak"]
            evi = row["has_evi"] == "yes"

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

        # STEP 2:
        # try to allocate the rest now
        # places from step 1 have become available
        self.fixed_set = None
        while self.vpl_movers_remaining():

            df = self.allocator.merchants_df.query(self.query)
            if df is None:
                return
            df = df.copy()
            df.sort_values(by=["sollicitatieNummer"], inplace=True, ascending=True)

            fixed = []
            wanted = []
            merch_dict = {}
            for _, row in df.iterrows():
                stands = row["plaatsen"]
                fixed += stands
                wanted += row["pref"]
                merch_dict[row["erkenningsNummer"]] = {
                    "fixed": stands,
                    "wanted": row["pref"],
                }

            # if A wants to go from 1 to 2 and B wants to go from 2 to 1
            res = TradePlacesSolver(merch_dict).get_position_traders()
            for erk in res:
                traded_stands = merch_dict[erk]["wanted"]
                self.allocator._allocate_stands_to_merchant(traded_stands, erk)

            # if two merchants want to move to the same spot
            # we have a conflict
            has_conflicts = len(set(wanted)) < len(wanted)

            # if the free postions list does
            # not change anymore we are out of 'save moves'
            # time to solve the conflicts if we can
            # NOTE: this will be the last iteration of this while loop
            if fixed == self.fixed_set:

                # first check if we have rejections
                has_rejections = False
                for _, row in df.iterrows():
                    erk = row["erkenningsNummer"]
                    stands = row["plaatsen"]
                    pref = row["pref"]
                    merchant_branches = row["voorkeur.branches"]
                    bak = row["has_bak"]
                    evi = row["has_evi"] == "yes"
                    valid_pref_stands = (
                        self.allocator.cluster_finder.find_valid_cluster(
                            pref,
                            size=len(stands),
                            merchant_branche=merchant_branches,
                            bak_merchant=bak,
                            evi_merchant=evi,
                            anywhere=False,
                        )
                    )
                    if len(valid_pref_stands) == 0:
                        has_rejections = True
                        break

                for _, row in df.iterrows():
                    erk = row["erkenningsNummer"]
                    stands = row["plaatsen"]
                    pref = row["pref"]
                    merchant_branches = row["voorkeur.branches"]
                    bak = row["has_bak"]
                    evi = row["has_evi"] == "yes"
                    expand = row["wants_expand"]
                    valid_pref_stands = (
                        self.allocator.cluster_finder.find_valid_cluster(
                            pref,
                            size=len(stands),
                            merchant_branche=merchant_branches,
                            bak_merchant=bak,
                            evi_merchant=evi,
                        )
                    )

                    if has_conflicts or has_rejections:
                        if expand:
                            self.allocator._prepare_expansion(
                                erk,
                                stands,
                                int(row["voorkeur.maximum"]),
                                merchant_branches,
                                bak,
                                evi,
                            )
                        # unable to solve conflict stay on fixed positions
                        try:
                            self.allocator._allocate_stands_to_merchant(stands, erk)
                        except MarketStandDequeueError:
                            try:
                                self.allocator._reject_merchant(
                                    erk, VPL_POSITION_NOT_AVAILABLE
                                )
                            except MerchantDequeueError:
                                clog.error(
                                    f"VPL plaatsen niet beschikbaar voor erkenningsNummer {erk}"
                                )
                    else:
                        if expand:
                            self.allocator._prepare_expansion(
                                erk,
                                valid_pref_stands,
                                int(row["voorkeur.maximum"]),
                                merchant_branches,
                                bak,
                                evi,
                            )
                        # no conflicts savely switch positions
                        self.allocator._allocate_stands_to_merchant(
                            valid_pref_stands, erk
                        )
                break
            else:
                # now allocate the vpl's that can move savely
                # meaning that the wanted positions do not intefere with
                # other fixed positions
                for _, row in df.iterrows():

                    erk = row["erkenningsNummer"]
                    stands = row["plaatsen"]
                    pref = row["pref"]
                    merchant_branches = row["voorkeur.branches"]
                    bak = row["has_bak"]
                    evi = row["has_evi"] == "yes"

                    valid_pref_stands = (
                        self.allocator.cluster_finder.find_valid_cluster(
                            pref,
                            size=len(stands),
                            merchant_branche=merchant_branches,
                            bak_merchant=bak,
                            evi_merchant=evi,
                            anywhere=False,
                        )
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
                            self.allocator._prepare_expansion(
                                erk,
                                stands_to_alloc,
                                int(row["voorkeur.maximum"]),
                                merchant_branches,
                                bak,
                                evi,
                            )
                        self.allocator._allocate_stands_to_merchant(
                            stands_to_alloc, erk
                        )
                    except Exception:
                        clog.error(
                            f"VPL plaatsen (verplaatsing) niet beschikbaar voor erkenningsNummer {erk}"
                        )

            self.fixed_set = fixed
        self.allocator.cluster_finder.set_check_branche_bak_evi(False)
