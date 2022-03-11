import pandas as pd
from kjk.utils import DebugRedisClient
from kjk.base import BaseAllocator
from kjk.base import STRATEGY_EXP_NONE
from kjk.base import STRATEGY_EXP_SOME
from kjk.base import STRATEGY_EXP_FULL
from kjk.rejection_reasons import MINIMUM_UNAVAILABLE
from kjk.rejection_reasons import PREF_NOT_AVAILABLE
from kjk.validation import ValidatorMixin
from kjk.logging import clog, log
from kjk.outputdata import ConvertToRejectionError
from kjk.moving_vpl import MovingVPLSolver

# from kjk.utils import AllocationDebugger

DEBUG = False


class Allocator(BaseAllocator, ValidatorMixin):
    """
    The base allocator object takes care of the data preparation phase
    and implements query methods
    So we can focus on the actual allocation phases here
    """

    def phase_01(self):
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
        self.reclaimed_number_stands = 0

    def phase_02(self):
        self.set_allocation_phase("Phase 2")
        log.info("")
        clog.info("--- ALLOCATIE FASE 2 ---")
        log.info("ondenemers (vpl) die niet willen verplaatsen:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_vpl_for_query("status == 'vpl' & will_move == 'no'")

    def phase_03(self):
        self.set_allocation_phase("Phase 3")
        log.info("")
        clog.info("--- ALLOCATIE FASE 3 ---")
        log.info("ondenemers (tvpl) die niet willen verplaatsen:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_vpl_for_query("status == 'tvpl' & will_move == 'no'")

    def phase_04(self):
        self.set_allocation_phase("Phase 4")
        log.info("")
        clog.info("--- ALLOCATIE FASE 4 ---")
        log.info("ondenemers (exp and expf) die niet mogen verplaatsen:")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_vpl_for_query(
            "(status == 'exp' | status == 'expf') & has_stands == True", print_df=False
        )

    def phase_05(self):
        self.set_allocation_phase("Phase 5")
        log.info("")
        clog.info("--- ALLOCATIE FASE 5 ---")
        log.info("ondenemers (vpl) die WEL willen verplaatsen.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        solver = MovingVPLSolver(
            self, "(status == 'vpl' | status == 'tvpl') & will_move == 'yes'"
        )
        solver.execute()

    def check_vpl_done(self):
        clog.info(
            "## Alle vpls zijn ingedeeld we gaan de plaatsen die nog vrij zijn verdelen"
        )
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        # double check all vpls allocated
        df = self.merchants_df.query("status == 'vpl'")
        if len(df) == 0:
            clog.info("check status OK all vpl's allocated.")
        else:
            clog.error("check status ERROR not all vpl's allocated.")

        # make sure merchants are sorted by sollnr
        self.merchants_df.sort_values(
            by=["sollicitatieNummer"], inplace=True, ascending=True
        )

    def phase_06(self):
        self.set_allocation_phase("Phase 6")
        log.info("")
        log.info("")
        clog.info("--- ALLOCATIE FASE 6 ---")
        log.info("Tijdelijke vasteplaatshouders zonder kraam (tvplz)")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_solls_for_query("status == 'tvplz'", print_df=False)

    def phase_07(self):
        self.set_allocation_phase("Phase 7")
        log.info("")
        log.info("")
        clog.info("--- ALLOCATIE FASE 7 ---")
        log.info("Experimentele ondernemers zonder kraam (exp en expf)")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        self._allocate_solls_for_query(
            "(status == 'exp' | status == 'expf') & has_stands == False", print_df=False
        )

    def phase_08(self):
        self.set_allocation_phase("Phase 8")
        log.info("")
        log.info("")
        clog.info("--- ALLOCATIE FASE 8 ---")
        log.info("Sollicitanten met verplichte branche op de A-lijst")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        list_mode = self.list_mode
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode} & branche_required == 'yes'",
            print_df=False,
        )

    def phase_09(self):
        self.set_allocation_phase("Phase 9")
        log.info("")
        log.info("")
        clog.info("--- ALLOCATIE FASE 9 ---")
        log.info("Sollicitanten die willen bakken op de A-lijst")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        list_mode = self.list_mode
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode} & has_bak == True", print_df=False
        )

    def phase_10(self):
        self.set_allocation_phase("Phase 10")
        log.info("")
        log.info("")
        clog.info("--- ALLOCATIE FASE 10 ---")
        log.info("Sollicitanten met een EVI op de A-lijst")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        list_mode = self.list_mode
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode} & has_evi == 'yes'", print_df=False
        )

    def phase_11(self):
        self.set_allocation_phase("Phase 11")
        log.info("")
        clog.info("--- ALLOCATIE FASE 11 ---")
        log.info("Overige sollicitanten op de A-lijst")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        list_mode = self.list_mode
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode}",
            print_df=False,
            check_branche_bak_evi=True,
        )

    def phase_12(self):
        self.set_allocation_phase("Phase 12")
        log.info("")
        clog.info("--- ALLOCATIE FASE 12 ---")
        log.info(
            "Alle ondernemers A-lijst ingedeeld, nu de uitbreidings fase voor vpl."
        )
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        if self.expanders_df is None:
            return
        df = self.expanders_df.query(
            "status == 'vpl' | status == 'tvpl' | status == 'tvplz'"
        )
        self._expand_for_merchants(df)

    def phase_13(self):
        self.set_allocation_phase("Phase 13")
        log.info("")
        clog.info("--- ALLOCATIE FASE 13 ---")
        log.info("Uitbreidings fase voor branche sollicitanten.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        if self.expanders_df is None:
            return
        list_mode = self.list_mode
        df = self.expanders_df.query(
            f"status == 'soll' & branche_required == 'yes' & {list_mode}"
        )
        self._expand_for_merchants(df)

    def phase_14(self):
        self.set_allocation_phase("Phase 14")
        log.info("")
        clog.info("--- ALLOCATIE FASE 14 ---")
        log.info("Uitbreidings fase voor BAK sollicitanten.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        if self.expanders_df is None:
            return
        list_mode = self.list_mode
        df = self.expanders_df.query(
            f"status == 'soll' & has_bak == True & {list_mode}"
        )
        self._expand_for_merchants(df)

    def phase_15(self):
        self.set_allocation_phase("Phase 15")
        log.info("")
        clog.info("--- ALLOCATIE FASE 15 ---")
        log.info("Uitbreidings fase voor EVI sollicitanten.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        if self.expanders_df is None:
            return
        list_mode = self.list_mode
        df = self.expanders_df.query(
            f"status == 'soll' & has_evi == 'yes' & {list_mode}"
        )
        self._expand_for_merchants(df)

    def phase_16(self):
        self.set_allocation_phase("Phase 16")
        log.info("")
        clog.info("--- ALLOCATIE FASE 16 ---")
        log.info("Uitbreidings fase voor Overige sollicitanten.")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        if self.expanders_df is None:
            return
        list_mode = self.list_mode
        df = self.expanders_df.query(f"status == 'soll' & {list_mode}")
        self._expand_for_merchants(df)

    def phase_25(self):
        # merchants who have 'anywhere' false
        # and do not have a preferred stand
        rejected = self.correct_preferences()
        self.reclaimed_number_stands = 0
        for r in rejected:
            try:
                stands_to_reclaim = self.market_output.convert_to_rejection(r)
                self.rejection_reasons.add_rejection_reason_for_merchant(
                    r, PREF_NOT_AVAILABLE
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

        # merchants who have less stands than min required
        rejected = self.correct_expansion()
        for r in rejected:
            try:
                stands_to_reclaim = self.market_output.convert_to_rejection(r)
                self.rejection_reasons.add_rejection_reason_for_merchant(
                    r, MINIMUM_UNAVAILABLE
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
            self.phase_12()
            self.phase_13()
            self.phase_14()
            self.phase_15()
            self.phase_16()

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

    def phase_26(self):
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

        self.phase_01()
        self.phase_02()
        self.phase_03()
        self.phase_04()
        self.phase_05()

        # all vpls should now be
        # allocated
        self.check_vpl_done()

        self.phase_06()
        self.phase_07()
        self.phase_08()
        self.phase_09()
        self.phase_10()
        self.phase_11()

        # expansion phases
        self.phase_12()
        self.phase_13()
        self.phase_14()
        self.phase_15()
        self.phase_16()

        # validation
        self.phase_25()

        self.set_mode_blist()

        self.phase_08()
        self.phase_09()
        self.phase_10()
        self.phase_11()

        # expansion phases
        self.phase_12()
        self.phase_13()
        self.phase_14()
        self.phase_15()
        self.phase_16()

        # validation
        self.phase_25()

        # rejection
        self.phase_26()

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
