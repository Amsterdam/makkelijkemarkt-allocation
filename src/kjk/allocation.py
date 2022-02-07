import pandas as pd
from kjk.utils import DebugRedisClient
from kjk.base import BaseAllocator
from kjk.base import STRATEGY_EXP_NONE
from kjk.base import STRATEGY_EXP_SOME
from kjk.base import STRATEGY_EXP_FULL
from kjk.base import MarketStandDequeueError
from kjk.base import MerchantDequeueError
from kjk.rejection_reasons import VPL_POSITION_NOT_AVAILABLE
from kjk.rejection_reasons import MINIMUM_UNAVAILABLE
from kjk.validation import ValidatorMixin
from kjk.logging import clog, log
from kjk.utils import TradePlacesSolver
from kjk.outputdata import ConvertToRejectionError

# from kjk.utils import AllocationDebugger

DEBUG = True


class Allocator(BaseAllocator, ValidatorMixin):
    """
    The base allocator object takes care of the data preparation phase
    and implements query methods
    So we can focus on the actual allocation phases here
    """

    def allocation_phase_01(self):
        clog.info("--- Makkelijkemarkt Allocatie ---")
        clog.info("--- ALLOCATIE FASE 1 ---")
        log.info("analyseer de markt en kijk (globaal) of er genoeg plaatsen zijn:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {} ".format(len(self.merchants_df)))

        max_demand = self.merchants_df["voorkeur.maximum"].sum()
        min_demand = self.merchants_df["voorkeur.minimum"].sum()
        num_available = len(self.positions_df)

        self.strategy = STRATEGY_EXP_NONE
        if max_demand < num_available:
            self.strategy = STRATEGY_EXP_FULL
        elif min_demand < num_available:
            self.strategy = STRATEGY_EXP_SOME

        log.info("")
        log.info("max {}".format(max_demand))
        log.info("min {}".format(int(min_demand)))
        log.info("beschikbaar {}".format(num_available))
        log.info("strategie: {}".format(self.strategy))

        # branche positions vs merchants rsvp
        self.branches_strategy = {}
        try:
            self.branches_df["verplicht"]
        except KeyError:
            clog.warning("--------------------------------------------")
            clog.warning("Field 'verplicht' missing from branches data")
            clog.warning("Assume default value 'False'")
            clog.warning("--------------------------------------------")
            self.branches_df["verplicht"] = False

        try:
            self.branches_df["maximumPlaatsen"]
        except KeyError:
            clog.warning("--------------------------------------------")
            clog.warning("Field 'maximumPlaatsen' missing from branches data")
            clog.warning("Assume default value '100'")
            clog.warning("--------------------------------------------")
            self.branches_df["maximumPlaatsen"] = 100

        # evi positions vs merchants rsvp
        evi_stands = self.get_evi_stands()
        evi_merchants = self.get_merchants_with_evi()
        self.evi_strategy = {
            "num_stands": len(evi_stands),
            "num_merchants": len(evi_merchants),
        }

    def allocation_phase_02(self):
        self.set_allocation_phase("Phase 2")
        log.info("")
        clog.info("--- ALLOCATIE FASE 2 ---")
        log.info("ondenemers (vpl) die niet willen verplaatsen of uitbreiden:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        df = self.merchants_df.query(
            "(status == 'exp' | status == 'expf') | (( status == 'vpl' | status == 'tvpl') & will_move == 'no')"
        )
        for _, row in df.iterrows():
            erk = row["erkenningsNummer"]
            try:
                stands = row["plaatsen"]
                expand = row["wants_expand"]
                merchant_branches = row["voorkeur.branches"]
                evi = row["has_evi"] == "yes"
                if expand:
                    self._prepare_expansion(
                        erk,
                        stands,
                        int(row["voorkeur.maximum"]),
                        merchant_branches,
                        evi,
                    )
                self._allocate_stands_to_merchant(stands, erk)
            except MarketStandDequeueError:
                try:
                    self._reject_merchant(erk, VPL_POSITION_NOT_AVAILABLE)
                except MerchantDequeueError:
                    clog.error(
                        f"VPL plaatsen niet beschikbaar voor erkenningsNummer {erk}"
                    )

    def allocation_phase_03(self):
        self.set_allocation_phase("Phase 3")
        log.info("")
        clog.info("--- ALLOCATIE FASE 3 ---")
        log.info("ondenemers (vpl) die WEL willen verplaatsen maar niet uitbreiden:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        df = self.merchants_df.query(
            "(status == 'vpl' | status == 'tvpl') & will_move == 'yes'"
        ).copy()
        df.sort_values(by=["sollicitatieNummer"], inplace=True, ascending=True)

        # moving vpl can not go to evi stands
        # if they do not have an evi, in later phases this is allowed
        # to fill up the market
        self.cluster_finder.set_prevent_evi(True)

        # STEP 1:
        # first allocate the vpl's that can not move to avoid conflicts
        failed = {}
        for _, row in df.iterrows():

            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            evi = row["has_evi"] == "yes"

            # some merchants have their own fixed stands as pref
            # don't ask me why we deal with this by checking overlap
            ignore_pref = any([x in stands for x in pref])

            valid_pref_stands = self.cluster_finder.find_valid_cluster(
                pref,
                size=len(stands),
                preferred=True,
                merchant_branche=merchant_branches,
                mode="any",
                evi_merchant=evi,
            )
            if len(valid_pref_stands) == 0 or ignore_pref:
                failed[erk] = (stands, row)

        for f in failed.keys():
            erk = f
            stands = stands_to_alloc = failed[f][0]
            row = failed[f][1]
            expand = row["wants_expand"]
            if expand:
                self._prepare_expansion(
                    erk, stands, int(row["voorkeur.maximum"]), merchant_branches, evi
                )
            try:
                self._allocate_stands_to_merchant(stands_to_alloc, erk)
            except MarketStandDequeueError:
                try:
                    self._reject_merchant(erk, VPL_POSITION_NOT_AVAILABLE)
                except MerchantDequeueError:
                    clog.error(
                        f"VPL plaatsen niet beschikbaar voor erkenningsNummer {erk}"
                    )

        # STEP 2:
        # try to allocate the rest now
        # places from step 1 have become available
        self.fixed_set = None
        while self.vpl_movers_remaining():

            df = self.merchants_df.query(
                "(status == 'vpl' | status == 'tvpl') & will_move == 'yes'"
            ).copy()
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
                self._allocate_stands_to_merchant(traded_stands, erk)

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
                    evi = row["has_evi"] == "yes"
                    valid_pref_stands = self.cluster_finder.find_valid_cluster(
                        pref,
                        size=len(stands),
                        preferred=True,
                        merchant_branche=merchant_branches,
                        mode="all",
                        evi_merchant=evi,
                    )
                    if len(valid_pref_stands) == 0:
                        has_rejections = True
                        break

                for _, row in df.iterrows():
                    erk = row["erkenningsNummer"]
                    stands = row["plaatsen"]
                    pref = row["pref"]
                    merchant_branches = row["voorkeur.branches"]
                    evi = row["has_evi"] == "yes"
                    expand = row["wants_expand"]
                    valid_pref_stands = self.cluster_finder.find_valid_cluster(
                        pref,
                        size=len(stands),
                        preferred=True,
                        merchant_branche=merchant_branches,
                        mode="all",
                        evi_merchant=evi,
                    )

                    if has_conflicts or has_rejections:
                        if expand:
                            self._prepare_expansion(
                                erk,
                                stands,
                                int(row["voorkeur.maximum"]),
                                merchant_branches,
                                evi,
                            )
                        # unable to solve conflict stay on fixed positions
                        try:
                            self._allocate_stands_to_merchant(stands, erk)
                        except MarketStandDequeueError:
                            try:
                                self._reject_merchant(erk, VPL_POSITION_NOT_AVAILABLE)
                            except MerchantDequeueError:
                                clog.error(
                                    f"VPL plaatsen niet beschikbaar voor erkenningsNummer {erk}"
                                )
                    else:
                        if expand:
                            self._prepare_expansion(
                                erk,
                                valid_pref_stands,
                                int(row["voorkeur.maximum"]),
                                merchant_branches,
                                evi,
                            )
                        # no conflicts savely switch positions
                        self._allocate_stands_to_merchant(valid_pref_stands, erk)
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
                    evi = row["has_evi"] == "yes"

                    valid_pref_stands = self.cluster_finder.find_valid_cluster(
                        pref,
                        size=len(stands),
                        preferred=True,
                        merchant_branche=merchant_branches,
                        mode="any",
                        evi_merchant=evi,
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
                            self._prepare_expansion(
                                erk,
                                stands_to_alloc,
                                int(row["voorkeur.maximum"]),
                                merchant_branches,
                                evi,
                            )
                        self._allocate_stands_to_merchant(stands_to_alloc, erk)
                    except Exception:
                        clog.error(
                            f"VPL plaatsen (verplaatsing) niet beschikbaar voor erkenningsNummer {erk}"
                        )

            self.fixed_set = fixed

        # restore the evi mode
        self.cluster_finder.set_prevent_evi(False)

    def allocation_phase_04(self):
        self.set_allocation_phase("Phase 4")
        log.info("")
        clog.info(
            "## Alle vpls's zijn ingedeeld we gaan de plaatsen die nog vrij zijn verdelen"
        )
        log.info("")
        clog.info("--- ALLOCATIE FASE 4 ---")
        log.info(
            "de soll's die een kraam willen in een verplichte branche en op de A-lijst staan"
        )
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # double check all vpls allocated
        df = self.merchants_df.query("status == 'vpl'")
        if len(df) == 0:
            clog.info("check status OK all vpl's allocated.")
        else:
            clog.error("check status ERROR not all vpl's allocated.")

        # make sure merchants are sorted, tvplz should go first
        self.merchants_df.sort_values(
            by=["sollicitatieNummer"], inplace=True, ascending=True
        )
        df_1 = self.merchants_df.query("status == 'tvplz'")
        df_2 = self.merchants_df.query("status != 'tvplz'")
        self.merchants_df = pd.concat([df_1, df_2])

        # A-list required branches
        self._allocate_branche_solls_for_query(
            "(status != 'exp' & status != 'expf') & alist == True & branche_required == 'yes'"
        )

    def allocation_phase_05(self):
        self.set_allocation_phase("Phase 5")
        log.info("")
        clog.info("--- ALLOCATIE FASE 5 ---")
        log.info("de soll's die een kraam willen met een EVI en op de A-lijst staan")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # A-list EVI
        self._allocate_evi_for_query(
            "(status != 'exp' & status != 'expf') & alist == True & has_evi == 'yes'"
        )

    def allocation_phase_06(self):
        self.set_allocation_phase("Phase 6")
        log.info("")
        clog.info("--- ALLOCATIE FASE 6 ---")
        log.info("B-lijst for verplichte branches")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # B-list required branches
        self._allocate_branche_solls_for_query(
            # "(status != 'exp' & status != 'expf') & alist != True & branche_required == 'yes' & has_evi != 'yes'"
            "(status != 'exp' & status != 'expf') & alist != True & branche_required == 'yes'"
        )

    def allocation_phase_07(self):
        self.set_allocation_phase("Phase 7")
        log.info("")
        clog.info("--- ALLOCATIE FASE 7 ---")
        log.info("B-lijst voor ondernemers met EVI")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # AB-list EVI
        self._allocate_evi_for_query(
            "(status != 'exp' & status != 'expf') & alist != True & has_evi == 'yes'"
        )

    def allocation_phase_08(self):
        self.set_allocation_phase("Phase 8")
        log.info("")
        clog.info("--- ALLOCATIE FASE 8 ---")
        log.info("Alle ondernemers ingedeeld, nu de uitbreidings fase voor vpl.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # get the alist people first
        vpls = self.expanders_df.query("status == 'vpl'")
        dataframes = [vpls]
        self._expand_for_merchants(dataframes)

    def allocation_phase_09(self):
        self.set_allocation_phase("Phase 9")
        log.info("")
        clog.info("--- ALLOCATIE FASE 9 ---")
        log.info(
            "B-lijst ingedeeld voor verplichte branches, overige solls op de A-lijst"
        )
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_solls_for_query(
            "(status != 'exp' & status != 'expf') & alist == True & branche_required != 'yes'",
            print_df=False,
        )

    def allocation_phase_10(self):
        self.set_allocation_phase("Phase 10")
        log.info("")
        clog.info("--- ALLOCATIE FASE 10 ---")
        log.info("Uitbreidings fase verplichte branches en EVI ondernemers.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # get the alist people first
        df_alist = self.expanders_df.query("alist == True & branche_required == 'yes'")
        df_blist = self.expanders_df.query("alist != True & branche_required == 'yes'")
        dataframes = [df_alist, df_blist]
        self._expand_for_merchants(dataframes)

        df_alist = self.expanders_df.query(
            "alist == True & branche_required != 'yes' & has_evi == 'yes'"
        )
        df_blist = self.expanders_df.query(
            "alist != True & branche_required != 'yes' & has_evi == 'yes'"
        )
        dataframes = [df_alist, df_blist]
        self._expand_for_merchants(dataframes)

    def allocation_phase_11(self):
        self.set_allocation_phase("Phase 11")
        log.info("")
        clog.info("--- ALLOCATIE FASE 11 ---")
        log.info("A-list gedaan, overige solls")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_solls_for_query(
            "(status != 'exp' & status != 'expf') & alist == False & branche_required != 'yes' & has_evi != 'yes'",
            print_df=False,
        )

    def allocation_phase_12(self):
        self.set_allocation_phase("Phase 12")
        log.info("")
        clog.info("--- ALLOCATIE FASE 12 ---")
        log.info("Alle ondernemers ingedeeld, nu de uitbreidings fase.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # get the alist people first
        df_alist = self.expanders_df.query(
            "alist == True & branche_required != 'yes' & has_evi != 'yes'"
        )
        df_blist = self.expanders_df.query(
            "alist != True & branche_required != 'yes' & has_evi != 'yes'"
        )
        dataframes = [df_alist, df_blist]
        self._expand_for_merchants(dataframes)

    def allocation_phase_13(self):
        self.set_allocation_phase("Phase 13")
        log.info("")
        clog.info("--- ALLOCATIE FASE  13 ---")
        log.info("Markt allocatie ingedeeld, nu de validatie.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # merchants who have 'anywhere' false
        # and do not have a preferred stand
        rejected = self.correct_preferences()
        self.reclaimed_number_stands = 0
        for r in rejected:
            try:
                stands_to_reclaim = self.market_output.convert_to_rejection(r)
            except ConvertToRejectionError:
                stands_to_reclaim = []
            self.reclaimed_number_stands += len(stands_to_reclaim)
            self.cluster_finder.set_stands_available(stands_to_reclaim)
            for std in stands_to_reclaim:
                df = self.back_up_stand_queue.query(f"plaatsId == '{std}'")
                self.positions_df = pd.concat([self.positions_df, df])
            mdf = self.back_up_merchant_queue.query(f"erkenningsNummer == '{r}'")
            self.merchants_df = pd.concat([self.merchants_df, mdf])

        # merchants who have less stands than min required
        rejected = self.correct_expansion()
        for r in rejected:
            try:
                stands_to_reclaim = self.market_output.convert_to_rejection(
                    r, reason=MINIMUM_UNAVAILABLE
                )
            except ConvertToRejectionError:
                stands_to_reclaim = []
            self.reclaimed_number_stands += len(stands_to_reclaim)
            self.cluster_finder.set_stands_available(stands_to_reclaim)
            for std in stands_to_reclaim:
                df = self.back_up_stand_queue.query(f"plaatsId == '{std}'")
                self.positions_df = pd.concat([self.positions_df, df])
            mdf = self.back_up_merchant_queue.query(f"erkenningsNummer == '{r}'")
            self.merchants_df = pd.concat([self.merchants_df, mdf])

        # fill in the reclaimed stands
        # all rules remain the same
        # until we don't have changes
        # in the number allocated stands
        self.num_open = 999999
        fill_iteration = 0
        while not self.market_filled():
            fill_iteration += 1
            stands = len(self.positions_df)
            clog.warning(
                f"Bezig met vullen van de markt. open plaatsen {stands}. ITERATIE: {fill_iteration}"
            )
            self.allocation_phase_04()
            self.allocation_phase_05()
            self.allocation_phase_06()
            self.allocation_phase_07()
            self.allocation_phase_09()
            self.allocation_phase_08()
            self.allocation_phase_10()
            self.allocation_phase_11()
            self.allocation_phase_12()

        self.validate_double_allocation()
        self.validate_evi_allocations()
        self.validate_branche_allocation()
        self.validate_expansion()
        self.validate_preferences()

    def market_filled(self):
        if self.num_open == len(self.positions_df):
            return True
        self.num_open = len(self.positions_df)
        return False

    def allocation_phase_14(self):
        self.set_allocation_phase("Phase 14")
        log.info("")
        clog.info("--- ALLOCATIE FASE 14 ---")
        log.info("Markt allocatie gevalideerd")
        log.info(
            "nog open plaatsen: {}".format(
                len(self.positions_df) + self.reclaimed_number_stands
            )
        )
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self.reject_remaining_merchants()

    def get_allocation(self):

        self.allocation_phase_01()
        self.allocation_phase_02()
        self.allocation_phase_03()
        self.allocation_phase_04()
        self.allocation_phase_05()
        self.allocation_phase_06()
        self.allocation_phase_07()
        self.allocation_phase_09()
        self.allocation_phase_08()
        self.allocation_phase_10()
        self.allocation_phase_11()
        self.allocation_phase_12()
        self.allocation_phase_13()
        self.allocation_phase_14()

        if DEBUG:
            json_file = self.market_output.to_json_file()
            debug_redis = DebugRedisClient()
            debug_redis.insert_test_result(json_file)

        return self.market_output.to_data()


if __name__ == "__main__":
    from inputdata import FixtureDataprovider

    dp = FixtureDataprovider("../../fixtures/dapp_20211030/a_input.json")
    a = Allocator(dp)
    a.get_allocation()
