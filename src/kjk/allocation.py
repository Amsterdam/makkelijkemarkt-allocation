import pandas as pd
from kjk.utils import DebugRedisClient
from kjk.base import BaseAllocator
from kjk.base import MarketStandDequeueError
from kjk.base import MerchantDequeueError
from kjk.base import VPL_POSITION_NOT_AVAILABLE
from kjk.validation import ValidatorMixin
from kjk.logging import clog, log
from kjk.utils import TradePlacesSolver

DEBUG = False


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

        log.info("")
        log.info("max {}".format(max_demand))
        log.info("min {}".format(int(min_demand)))
        log.info("beschikbaar {}".format(num_available))

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

        if len(self.branches_df) > 0:
            df = self.branches_df.query("verplicht == True")
            for index, row in df.iterrows():
                br_id = row["brancheId"]
                br = self.get_merchant_for_branche(br_id)
                std = self.get_stand_for_branche(br_id)
                try:
                    maxi = int(row["maximumPlaatsen"])
                except ValueError:
                    clog.warning("--------------------------------------------")
                    clog.warning(
                        f"Field 'maximumPlaatsen' is Nan for branche id: {br_id}"
                    )
                    clog.warning("Assume default value '100'")
                    clog.warning("--------------------------------------------")
                    maxi = 100
                self.branches_strategy[br_id] = {
                    "max": int(maxi),
                    "num_stands": len(std),
                    "num_merchants": len(br),
                    "will_fit": len(std) > len(br),
                }

        # evi positions vs merchants rsvp
        evi_stands = self.get_evi_stands()
        evi_merchants = self.get_merchants_with_evi()
        self.evi_strategy = {
            "num_stands": len(evi_stands),
            "num_merchants": len(evi_merchants),
        }

    def _prepare_expansion(self, erk, stands, size, merchant_branches, evi):
        expansion_candidates = self.cluster_finder.find_valid_expansion(
            stands,
            total_size=size,
            merchant_branche=merchant_branches,
            evi_merchant=evi,
            ignore_check_available=stands,
        )
        for exp in expansion_candidates:
            self.cluster_finder.set_stands_reserved(exp)
        if len(expansion_candidates) > 0 and self.expansion_mode == "greedy":
            self._allocate_stands_to_merchant(
                expansion_candidates[0], erk, dequeue_merchant=False
            )

    def allocation_phase_02(self):
        log.info("")
        clog.info("--- ALLOCATIE FASE 2 ---")
        log.info("ondenemers (vpl) die niet willen verplaatsen of uitbreiden:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        df = self.merchants_df.query(
            "(status == 'exp' | status == 'expf') | (( status == 'vpl' | status == 'tvpl') & will_move == 'no')"
        )
        for index, row in df.iterrows():
            try:
                erk = row["erkenningsNummer"]
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
        log.info("")
        clog.info("--- ALLOCATIE FASE 3 ---")
        log.info("ondenemers (vpl) die WEL willen verplaatsen maar niet uitbreiden:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        df = self.merchants_df.query(
            "(status == 'vpl' | status == 'tvpl') & will_move == 'yes'"
        ).copy()
        df.sort_values(by=["sollicitatieNummer"], inplace=True, ascending=True)

        # STEP 1:
        # first allocate the vpl's that can not move to avoid conflicts
        failed = {}
        for index, row in df.iterrows():

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
            self._allocate_stands_to_merchant(stands_to_alloc, erk)

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
            for index, row in df.iterrows():
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
                for index, row in df.iterrows():
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

                for index, row in df.iterrows():
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
                        self._allocate_stands_to_merchant(stands, erk)
                    else:
                        if expand:
                            self._prepare_expansion(
                                erk,
                                stands,
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
                for index, row in df.iterrows():

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
                                stands,
                                int(row["voorkeur.maximum"]),
                                merchant_branches,
                                evi,
                            )
                        self._allocate_stands_to_merchant(stands_to_alloc, erk)
                    except Exception:
                        print(erk, stands_to_alloc)

            self.fixed_set = fixed

    def allocation_phase_04(self):
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
        log.info("")
        clog.info("--- ALLOCATIE FASE 6 ---")
        log.info("B-lijst for verplichte branches")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # B-list required branches
        self._allocate_branche_solls_for_query(
            "(status != 'exp' & status != 'expf') & alist != True & branche_required == 'yes' & has_evi != 'yes'"
        )

    def allocation_phase_07(self):
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
        log.info("")
        clog.info("--- ALLOCATIE FASE 8 ---")
        log.info("Alle ondernemers ingedeeld, nu de uitbreidings fase voor vpl.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # get the alist people first
        vpls = self.expanders_df.query("status == 'vpl'")
        dataframes = [vpls]
        for df in dataframes:
            for index, row in df.iterrows():
                erk = row["erkenningsNummer"]
                stands = row["plaatsen"]
                merchant_branches = row["voorkeur.branches"]
                evi = row["has_evi"] == "yes"
                maxi = row["voorkeur.maximum"]

                assigned_stands = self.market_output.get_assigned_stands_for_merchant(
                    erk
                )
                if assigned_stands is not None:
                    stands = self.cluster_finder.find_valid_expansion(
                        assigned_stands,
                        total_size=int(maxi),
                        merchant_branche=merchant_branches,
                        evi_merchant=evi,
                        ignore_check_available=assigned_stands,
                    )
                    if len(stands) > 0:
                        self._allocate_stands_to_merchant(
                            stands[0], erk, dequeue_merchant=False
                        )

    def allocation_phase_09(self):
        log.info("")
        clog.info("--- ALLOCATIE FASE 9 ---")
        log.info(
            "B-lijst ingedeeld voor verplichte branches, overige solls op de A-lijst"
        )
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_solls_for_query(
            # "alist == True & branche_required != 'yes' & has_evi != 'yes'"
            "(status != 'exp' & status != 'expf') & alist == True & branche_required != 'yes'",
            print_df=False,
        )

    def allocation_phase_10(self):
        log.info("")
        clog.info("--- ALLOCATIE FASE 10 ---")
        log.info("A-list gedaan, overige solls")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_solls_for_query(
            "(status != 'exp' & status != 'expf') & alist == False & branche_required != 'yes' & has_evi != 'yes'"
        )

    def allocation_phase_11(self):
        log.info("")
        clog.info("--- ALLOCATIE FASE 11 ---")
        log.info("Alle ondernemers ingedeeld, nu de uitbreidings fase.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # get the alist people first
        df_alist = self.expanders_df.query("alist == True")
        df_blist = self.expanders_df.query("alist != True")
        dataframes = [df_alist, df_blist]
        for df in dataframes:
            for index, row in df.iterrows():
                erk = row["erkenningsNummer"]
                stands = row["plaatsen"]
                merchant_branches = row["voorkeur.branches"]
                evi = row["has_evi"] == "yes"
                maxi = row["voorkeur.maximum"]
                status = row["status"]

                # exp, expf can not expand
                if status in ("exp", "expf"):
                    continue

                assigned_stands = self.market_output.get_assigned_stands_for_merchant(
                    erk
                )
                if assigned_stands is not None:
                    stands = self.cluster_finder.find_valid_expansion(
                        assigned_stands,
                        total_size=int(maxi),
                        merchant_branche=merchant_branches,
                        evi_merchant=evi,
                        ignore_check_available=assigned_stands,
                    )
                    if len(stands) > 0:
                        self._allocate_stands_to_merchant(
                            stands[0], erk, dequeue_merchant=False
                        )

    def allocation_phase_12(self):
        log.info("")
        clog.info("--- ALLOCATIE FASE  12 ---")
        log.info("Markt allocatie ingedeeld, nu de validatie.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self.validate_double_allocation()
        self.validate_evi_allocations()
        self.validate_branche_allocation()
        self.validate_expansion()

    def allocation_phase_13(self):
        log.info("")
        clog.info("--- ALLOCATIE FASE 13 ---")
        log.info("Markt allocatie gevalideerd")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
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
        self.allocation_phase_08()
        self.allocation_phase_09()
        self.allocation_phase_10()
        self.allocation_phase_11()
        self.allocation_phase_12()
        self.allocation_phase_13()

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
