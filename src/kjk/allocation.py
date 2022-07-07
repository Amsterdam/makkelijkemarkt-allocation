import pandas as pd
from kjk.utils import DebugRedisClient
from kjk.base import MODE_ALIST, MODE_BLIST, BaseAllocator
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

    def _phase_msg(self, phase_id, message):
        self.set_allocation_phase(f"Phase {phase_id}")
        log.info("")
        clog.info(f"--- ALLOCATIE FASE {phase_id} ---")
        log.info(message)
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {} ".format(len(self.merchants_df)))

    def analyze_market(self):

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

    def vpl_not_moving(self):
        self._allocate_vpl_for_query("status == 'vpl' & will_move == 'no'")

    def tvpl_not_moving(self):
        self._allocate_vpl_for_query("status == 'tvpl' & will_move == 'no'")

    def exp_not_moving(self):
        self._allocate_vpl_for_query(
            "(status == 'exp' | status == 'expf') & has_stands == True", print_df=False
        )
        self._allocate_vpl_for_query(
            "(status == 'eb') & has_stands == True", print_df=False
        )

    def vpl_moving(self):
        self.set_allocation_phase("Phase 5")
        log.info("")
        clog.info("--- ALLOCATIE FASE 5 ---")
        log.info("nog open plaatsen: {}".format(len(self.positions_df)))
        log.info("ondenemers nog niet ingedeeld: {}".format(len(self.merchants_df)))

        solver = MovingVPLSolver(
            self, "(status == 'vpl' | status == 'tvpl') & will_move == 'yes'"
        )
        solver.execute(print_df=False)
        self._add_vpl_moved_status_to_expanders(solver.get_successful_movers())

    def check_vpl_done(self):
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

    def tvplz(self):
        self.cluster_finder.set_check_branche_bak_evi(True)
        self._allocate_solls_for_query("status == 'tvplz'", print_df=False)
        self.cluster_finder.set_check_branche_bak_evi(False)

    def exp_no_stands(self):
        self._allocate_solls_for_query(
            "(status == 'exp' | status == 'expf') & has_stands == False", print_df=False
        )

    def branche_soll(self, list_mode=MODE_ALIST):
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode} & branche_required == 'yes'",
            print_df=False,
        )

    def bak_soll(self, list_mode=MODE_ALIST):
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode} & has_bak == True", print_df=False
        )
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode} & bak_type == 'bak-licht'", print_df=False
        )

    def evi_soll(self, list_mode=MODE_ALIST):
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode} & has_evi == 'yes'", print_df=False
        )

    def regular_soll(self, list_mode=MODE_ALIST):
        self._allocate_solls_for_query(
            f"status == 'soll' & {list_mode}",
            print_df=False,
            check_branche_bak_evi=True,
        )

    def expand_vpl(self):
        self.cluster_finder.set_check_branche_bak_evi(True)
        if self.expanders_df is None:
            return
        df = self.expanders_df.query(
            "(status == 'vpl' | status == 'tvpl' | status == 'tvplz' | status == 'eb') & vpl_did_move == False"
        )
        self._expand_for_merchants(df)
        df = self.expanders_df.query(
            "(status == 'vpl' | status == 'tvpl' | status == 'tvplz' | status == 'eb') & vpl_did_move == True"
        )
        self._expand_for_merchants(df)
        self.cluster_finder.set_check_branche_bak_evi(False)

    def expand_branche_soll(self, list_mode=MODE_ALIST):
        if self.expanders_df is None:
            return
        df = self.expanders_df.query(
            f"status == 'soll' & branche_required == 'yes' & {list_mode}"
        )
        self._expand_for_merchants(df)

    def expand_bak_soll(self, list_mode=MODE_ALIST):
        if self.expanders_df is None:
            return
        df = self.expanders_df.query(
            f"status == 'soll' & has_bak == True & {list_mode}"
        )
        self._expand_for_merchants(df)
        df = self.expanders_df.query(
            f"status == 'soll' & bak_type == 'bak-licht' & {list_mode}"
        )
        self._expand_for_merchants(df)

    def expand_evi_soll(self, list_mode=MODE_ALIST):
        if self.expanders_df is None:
            return
        df = self.expanders_df.query(
            f"status == 'soll' & has_evi == 'yes' & {list_mode}"
        )
        self._expand_for_merchants(df)

    def expand_regular_soll(self, list_mode=MODE_ALIST):
        if self.expanders_df is None:
            return
        df = self.expanders_df.query(f"status == 'soll' & {list_mode}")
        self._expand_for_merchants(df)

    def validate(self):
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

        # fill the reclaimed stands, sort by soll_nr first
        self.merchants_df.sort_values(
            by=["sollicitatieNummer"], inplace=True, ascending=True
        )
        self._allocate_solls_for_query("all")

        self.validate_double_allocation()
        self.validate_evi_allocations()
        self.validate_branche_allocation()
        self.validate_expansion()
        self.validate_preferences()

    def enable_expansion(self, message=""):
        self.num_open = 999999
        self.expansion_iteration = 0
        self.expansion_message = message

    def expansion_finished(self):
        if self.num_open == len(self.positions_df):
            return True
        self.num_open = len(self.positions_df)
        self.expansion_iteration += 1
        iter_nr = self.expansion_iteration
        msg = self.expansion_message
        clog.info(f"Uitbreidingsfase iteratie nr {iter_nr} context: {msg}")
        return False

    def reject(self):
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

        clog.info("--- Makkelijkemarkt Allocatie ---")
        self._phase_msg(
            1, "analyseer de markt en kijk (globaal) of er genoeg plaatsen zijn:"
        )
        self.analyze_market()

        self._phase_msg(2, "ondenemers (vpl) die niet willen verplaatsen:")
        self.vpl_not_moving()

        self._phase_msg(3, "ondenemers (tvpl) die niet willen verplaatsen:")
        self.tvpl_not_moving()

        self._phase_msg(4, "ondenemers (exp, expf and eb) die niet mogen verplaatsen:")
        self.exp_not_moving()

        self._phase_msg(5, "ondenemers (vpl) die WEL willen verplaatsen.")
        self.vpl_moving()

        # all vpls should now be allocated
        self._phase_msg(
            "",
            "## Alle vpls zijn ingedeeld we gaan de plaatsen die nog vrij zijn verdelen",
        )
        self.check_vpl_done()

        self._phase_msg(6, "Tijdelijke vasteplaatshouders zonder kraam (tvplz)")
        self.tvplz()

        self._phase_msg(7, "Experimentele ondernemers zonder kraam (exp en expf)")
        self.exp_no_stands()

        self._phase_msg(8, "Sollicitanten met verplichte branche op de A-lijst")
        self.branche_soll(list_mode=MODE_ALIST)

        self._phase_msg(9, "Sollicitanten met BAK op de A-lijst")
        self.bak_soll(list_mode=MODE_ALIST)

        self._phase_msg(10, "Sollicitanten met een EVI op de A-lijst")
        self.evi_soll(list_mode=MODE_ALIST)

        self._phase_msg(11, "Overige sollicitanten op de A-lijst")
        self.regular_soll(list_mode=MODE_ALIST)

        # expansion alist vpl and branche-bak-evi soll
        self.enable_expansion("VPL + BRANCHE-BAK-EVI soll A-lijst")
        while not self.expansion_finished():
            self._phase_msg(12, "Uitbreidings fase voor vpl.")
            self.expand_vpl()

            self._phase_msg(13, "Uitbreidings fase voor branche sollicitanten.")
            self.expand_branche_soll(list_mode=MODE_ALIST)

            self._phase_msg(14, "Uitbreidings fase voor BAK sollicitanten.")
            self.expand_bak_soll(list_mode=MODE_ALIST)

            self._phase_msg(15, "Uitbreidings fase voor EVI sollicitanten.")
            self.expand_evi_soll(list_mode=MODE_ALIST)

        self._phase_msg(16, "Sollicitanten met verplichte branche op de B-lijst")
        self.branche_soll(list_mode=MODE_BLIST)

        self._phase_msg(17, "Sollicitanten met BAK op de B-lijst")
        self.bak_soll(list_mode=MODE_BLIST)

        self._phase_msg(18, "Sollicitanten met een EVI op de B-lijst")
        self.evi_soll(list_mode=MODE_BLIST)

        # expansion blist branche-bak-evi soll
        self.enable_expansion("BRANCHE-BAK-EVI soll B-lijst")
        while not self.expansion_finished():
            self._phase_msg(19, "Uitbreidings fase voor branche sollicitanten.")
            self.expand_branche_soll(list_mode=MODE_BLIST)

            self._phase_msg(20, "Uitbreidings fase voor BAK sollicitanten.")
            self.expand_bak_soll(list_mode=MODE_BLIST)

            self._phase_msg(21, "Uitbreidings fase voor EVI sollicitanten.")
            self.expand_evi_soll(list_mode=MODE_BLIST)

        # expansion alist soll
        self.enable_expansion("Overige soll A-lijst")
        while not self.expansion_finished():
            self._phase_msg(22, "Uitbreidings fase overige sollicitanten.")
            self.expand_regular_soll(list_mode=MODE_ALIST)

        self._phase_msg(23, "Overige sollicitanten op de B-lijst")
        self.regular_soll(list_mode=MODE_BLIST)

        # expansion blist soll
        self.enable_expansion("Overige soll B-lijst")
        while not self.expansion_finished():
            self._phase_msg(24, "Uitbreidings fase overige sollicitanten.")
            self.expand_regular_soll(list_mode=MODE_BLIST)

        # validation
        self.validate()

        # rejection
        self.reject()

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
