from pprint import pprint
import pandas as pd
from datetime import date
from kjk.outputdata import MarketArrangement
from kjk.utils import MarketStandClusterFinder
from kjk.utils import DebugRedisClient
from kjk.base import *

DEBUG = False


class Allocator(BaseAllocator):
    """
    The base allocator object takes care of the data preparation phase
    and implements query methods
    So we can focus on the actual allocation phases here
    """

    def allocation_phase_00(self):
        print("\n--- START ALLOCATION FASE 0")
        print("analyseer de markt en kijk (globaal) of er genoeg plaatsen zijn:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        max_demand = self.merchants_df["voorkeur.maximum"].sum()
        min_demand = self.merchants_df["voorkeur.minimum"].sum()
        num_available = len(self.positions_df)

        self.strategy = STRATEGY_EXP_NONE
        if max_demand < num_available:
            self.strategy = STRATEGY_EXP_FULL
        elif min_demand < num_available:
            self.strategy = STRATEGY_EXP_SOME

        print("max ", max_demand)
        print("min ", int(min_demand))
        print("beschikbaar ", num_available)
        print("strategie: ", self.strategy)

        # branche positions vs merchants rsvp
        self.branches_strategy = {}
        if len(self.branches_df) > 0:
            df = self.branches_df.query("verplicht == True")
            for index, row in df.iterrows():
                br_id = row["brancheId"]
                br = self.get_merchant_for_branche(br_id)
                std = self.get_stand_for_branche(br_id)
                self.branches_strategy[br_id] = {
                    "max": int(row["maximumPlaatsen"]),
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

    def allocation_phase_01(self):
        print("\n--- START ALLOCATION FASE 1")
        print("ondenemers (vpl) die niet willen verplaatsen of uitbreiden:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        df = self.merchants_df.query(
            "(status == 'vpl' | status == 'exp' | status == 'tvpl') & will_move == 'no' & wants_expand == False"
        )
        for index, row in df.iterrows():
            try:
                erk = row["erkenningsNummer"]
                stands = row["plaatsen"]
                self._allocate_stands_to_merchant(stands, erk)
            except MarketStandDequeueError as e:
                self._reject_merchant(erk, VPL_POSITION_NOT_AVAILABLE)

    def allocation_phase_02(self):
        print("\n--- FASE 2")
        print("ondenemers (vpl) die NIET willen verplaatsen maar WEL uitbreiden:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        # NOTE: save the expanders df for later, we need them for the extra stands iterations in tight strategies
        df = self.merchants_df.query(
            "(status == 'vpl' | status == 'exp' | status == 'tvpl') & will_move == 'no' & wants_expand == True"
        ).copy()
        df.sort_values(by=["sollicitatieNummer"], inplace=True, ascending=False)
        for index, row in df.iterrows():
            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            merchant_branches = row["voorkeur.branches"]
            evi = row["has_evi"] == "yes"
            # if we have plenty space on the merket reward the expansion now
            if self.strategy == STRATEGY_EXP_FULL:
                stands = self.cluster_finder.find_valid_expansion(
                    row["plaatsen"],
                    total_size=int(row["voorkeur.maximum"]),
                    merchant_branche=merchant_branches,
                    evi_merchant=evi,
                )
                if len(stands) > 0:
                    stands = stands[0]
                else:
                    stands = row["plaatsen"]  # no expansion possible
            self._allocate_stands_to_merchant(stands, erk)

    def allocation_phase_03(self):
        print("\n--- FASE 3")
        print("ondenemers (vpl) die WEL willen verplaatsen maar niet uitbreiden:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        df = self.merchants_df.query(
            "(status == 'vpl' | status == 'exp' | status == 'tvpl') & will_move == 'yes' & wants_expand == False"
        ).copy()
        df.sort_values(by=["sollicitatieNummer"], inplace=True, ascending=False)

        failed = {}
        for index, row in df.iterrows():

            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            maxi = row["voorkeur.maximum"]

            valid_pref_stands = self.cluster_finder.find_valid_cluster(
                pref,
                size=len(stands),
                preferred=True,
                merchant_branche=merchant_branches,
                mode="any",
            )
            if len(valid_pref_stands) == 0:
                failed[erk] = stands

        # first allocate the vpl's that can not move to avoid conflicts
        for f in failed.keys():
            erk = f
            stands_to_alloc = failed[f]
            self._allocate_stands_to_merchant(stands_to_alloc, erk)

        # reload the dataframe with the unsuccessful movers removed from the stack
        df = self.merchants_df.query(
            "(status == 'vpl' | status == 'exp' | status == 'tvpl') & will_move == 'yes' & wants_expand == False"
        ).copy()
        df.sort_values(by=["sollicitatieNummer"], inplace=True, ascending=False)

        for index, row in df.iterrows():

            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            maxi = row["voorkeur.maximum"]
            evi = row["has_evi"] == "yes"

            valid_pref_stands = self.cluster_finder.find_valid_cluster(
                pref,
                size=len(stands),
                preferred=True,
                merchant_branche=merchant_branches,
                mode="any",
                evi_merchant=evi,
            )
            if len(valid_pref_stands) < len(stands):
                stands_to_alloc = stands
            else:
                stands_to_alloc = valid_pref_stands
            self._allocate_stands_to_merchant(stands_to_alloc, erk)

    def allocation_phase_04(self):
        print("\n--- FASE 4")
        print("de vpl's die willen uitbreiden en verplaatsen")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        df = self.merchants_df.query(
            "status == 'vpl' & wants_expand == True & will_move == 'yes'"
        )
        for index, row in df.iterrows():

            erk = row["erkenningsNummer"]
            stands = row["plaatsen"]
            pref = row["pref"]
            merchant_branches = row["voorkeur.branches"]
            maxi = row["voorkeur.maximum"]
            evi = row["has_evi"] == "yes"

            valid_pref_stands = []
            if self.strategy == STRATEGY_EXP_FULL:
                # expansion possible on preferred new location?
                valid_pref_stands = self.cluster_finder.find_valid_cluster(
                    pref,
                    size=int(maxi),
                    preferred=True,
                    merchant_branche=merchant_branches,
                    mode="any",
                    evi_merchant=evi,
                )
                if len(valid_pref_stands) == 0:
                    # expansion possible on 'old' location?
                    valid_pref_stands = self.cluster_finder.find_valid_expansion(
                        row["plaatsen"],
                        total_size=int(row["voorkeur.maximum"]),
                        merchant_branche=merchant_branches,
                        evi_merchant=evi,
                    )
                    if len(valid_pref_stands) > 0:
                        valid_pref_stands = valid_pref_stands[0]

            if len(valid_pref_stands) < len(stands):
                stands_to_alloc = stands
            else:
                stands_to_alloc = valid_pref_stands
            self._allocate_stands_to_merchant(stands_to_alloc, erk)

    def allocation_phase_05(self):
        print(
            "\n## Alle vpls's zijn ingedeeld we gaan de plaatsen die nog vrij zijn verdelen"
        )
        print("\n--- FASE 5")
        print(
            "de soll's die een kraam willen in een verplichte branche en op de A-lijst staan"
        )
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        # double check all vpls allocated
        df = self.merchants_df.query("status == 'vpl'")
        if len(df) == 0:
            print("check status OK all vpl's allocated.")
        else:
            print("check status ERROR not all vpl's allocated.")

        # make sure merchants are sorted, tvplz should go first
        self.merchants_df.sort_values(
            by=["sollicitatieNummer"], inplace=True, ascending=False
        )
        df_1 = self.merchants_df.query("status == 'tvplz'")
        df_2 = self.merchants_df.query("status != 'tvplz'")
        self.merchants_df = pd.concat([df_1, df_2])

        # A-list required branches
        self._allocate_branche_solls_for_query(
            "alist == True & branche_required == 'yes'"
        )

        # A-list EVI
        self._allocate_evi_for_query("alist == True & has_evi == 'yes'")

    def allocation_phase_06(self):
        print("\n--- FASE 6")
        print(
            "A-lijst ingedeeld voor verplichte branches, nu de B-lijst for verplichte branches"
        )
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        # B-list required branches
        self._allocate_branche_solls_for_query(
            "alist != True & branche_required == 'yes'"
        )

        # AB-list EVI
        self._allocate_evi_for_query("alist != True & has_evi == 'yes'")

    def allocation_phase_07(self):
        print("\n--- FASE 7")
        print("B-lijst ingedeeld voor verplichte branches, overige solls op de A-lijst")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        self._allocate_solls_for_query(
            "alist == True & branche_required != 'yes' & has_evi != 'yes'"
        )

    def allocation_phase_08(self):
        print("\n--- FASE 8")
        print("A-list gedaan, overige solls")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        self._allocate_solls_for_query(
            "alist == False & branche_required != 'yes' & has_evi != 'yes'"
        )

    def allocation_phase_09(self):
        print("\n--- FASE 9")
        print("Alle ondernemers ingedeeld, nu de uitbreidings fase.")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        # STRATEGY_EXP_NONE means no expansion possible (market space is thight)
        # STRATEGY_EXP_FULL means expansion already done during previous phases
        if self.strategy == STRATEGY_EXP_SOME:
            for index, row in self.expanders_df.iterrows():
                erk = row["erkenningsNummer"]
                stands = row["plaatsen"]
                merchant_branches = row["voorkeur.branches"]
                evi = row["has_evi"] == "yes"

                assigned_stands = self.market_output.get_assigned_stands_for_merchant(
                    erk
                )
                stands = self.cluster_finder.find_valid_expansion(
                    assigned_stands,
                    total_size=int(row["voorkeur.maximum"]),
                    merchant_branche=merchant_branches,
                    evi_merchant=evi,
                    ignore_check_available=assigned_stands,
                )
                print(
                    erk, " -> ", assigned_stands, row["voorkeur.maximum"], " : ", stands
                )
                if len(stands) > 0:
                    self._allocate_stands_to_merchant(
                        stands[0], erk, dequeue_merchant=False
                    )

    def allocation_phase_10(self):
        print("\n--- FASE 10")
        print("Markt allocatie ingedeeld, nu de validatie.")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

    def allocation_phase_11(self):
        print("\n--- FASE 11")
        print("Markt allocatie gevalideerd")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        self.reject_remaining_merchants()

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

           reminder: aLijst, vervangers
        """

        self.allocation_phase_00()
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
