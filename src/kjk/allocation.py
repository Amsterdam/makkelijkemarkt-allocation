from pprint import pprint
import pandas as pd
from datetime import date
from kjk.outputdata import MarketArrangement
from kjk.utils import MarketStandClusterFinder
from kjk.utils import DebugRedisClient
from kjk.base import *

DEBUG = True

class Allocator(BaseAllocator):
    """
    The base allocator object takes care of the data preparation phase
    and implements query methods
    So we can focus on the actual allocation phases here
    """
    def allocation_phase_0(self):
        print("\n--- START ALLOCATION FASE 1")
        print("analyseer de markt en kijk of er genoeg plaatsen zijn:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))
        
        max_demand = self.merchants_df['voorkeur.maximum'].sum()
        min_demand = self.merchants_df['voorkeur.minimum'].sum()
        num_available = len(self.positions_df)
        
        print("max ",max_demand)
        print("min ", int(min_demand))
        print("beschikbaar ", num_available)

        df = self.branches_df.query("verplicht == True")
        #print(df.info())
        for index, row in df.iterrows():
            br_id = row['brancheId']
            br = self.get_merchant_for_branche(br_id)
            std = self.get_stand_for_branche(br_id)
            #print("branche: ", br_id)
            #print("maximaal:", int(row['maximumPlaatsen']))
            #print("aantal ondernemers", len(br))
            #print("aantal standplaatsen: ", len(std))
            #print(" - - - ")

        evi_stands = self.get_evi_stands()
        # print(evi_stands)
        num_evi = self.get_merchants_with_evi() 
        # print(num_evi)
        

    def allocation_phase_1(self):
        print("\n--- START ALLOCATION FASE 1")
        print("ondenemers (vpl) die niet willen verplaatsen of uitbreiden:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        df = self.merchants_df.query("(status == 'vpl' | status == 'exp' | status == 'tvpl') & will_move == 'no' & wants_expand == False")
        print(df.query("status == 'exp'"))
        for index, row in df.iterrows():
            erk = row['erkenningsNummer']
            stands = row['plaatsen']
            self.market_output.add_allocation(erk, stands, self.merchant_object_by_id(erk))
            try:
                self.dequeue_marchant(erk)
            except KeyError as e:
                raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
            for st in stands:
                self.dequeue_market_stand(st)

    def allocation_phase_2(self):
        print("\n--- FASE 2")
        print("ondenemers (vpl) die NIET willen verplaatsen maar WEL uitbreiden:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        # NOTE: save the expanders df for later, we need them for the extra stands iterations
        self.expanders_df = self.merchants_df.query("(status == 'vpl' | status == 'exp' | status == 'tvpl') & will_move == 'no' & wants_expand == True").copy()
        self.expanders_df.sort_values(by=['sollicitatieNummer'], inplace=True, ascending=False)
        for index, row in self.expanders_df.iterrows():
            erk = row['erkenningsNummer']
            stands = row['plaatsen']
            self.market_output.add_allocation(erk, stands, self.merchant_object_by_id(erk))
            try:
                self.dequeue_marchant(erk)
            except KeyError as e:
                raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
            for st in stands:
                self.dequeue_market_stand(st)

    def allocation_phase_3(self):
        print("\n--- FASE 3")
        print("ondenemers (vpl) die WEL willen verplaatsen maar niet uitbreiden:")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))
        df = self.merchants_df.query("(status == 'vpl' | status == 'exp' | status == 'tvpl') & will_move == 'yes' & wants_expand == False").copy()
        df.sort_values(by=['sollicitatieNummer'], inplace=True, ascending=False)
        for index, row in df.iterrows():

            erk = row['erkenningsNummer']
            stands = row['plaatsen']
            pref = row['pref']
            merchant_branches = row['voorkeur.branches']
            maxi = row['voorkeur.maximum']

            valid_pref_stands = []
            for i, p in enumerate(pref):
                stand = self.positions_df.query(f"plaatsId == '{p}'")
                if len(stand) > 0:
                    stand_branches = self.get_branches_for_stand(p)
                    if len(stand_branches) == 0:
                        # no branched stand, allocate!
                        valid_pref_stands.append(p)
                    else:
                        # stand has branches, check compatible
                        branche_overlap = list(set(merchant_branches).intersection(set(stand_branches)))
                        if len(branche_overlap) > 0:
                            valid_pref_stands.append(p)
                if len(valid_pref_stands) == len(stands):
                    break

            if len(valid_pref_stands) < len(stands):
                stands_to_alloc = stands
            else:
                stands_to_alloc = valid_pref_stands

            self.market_output.add_allocation(erk, stands_to_alloc, self.merchant_object_by_id(erk))
            try:
                self.dequeue_marchant(erk)
            except KeyError as e:
                raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
            for st in stands:
                self.dequeue_market_stand(st)

    def allocation_phase_4(self):
        print("\n--- FASE 4")
        print("de vpl's die willen uitbreiden en verplaatsen")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        df = self.merchants_df.query("status == 'vpl' & wants_expand == True & will_move == 'yes'")
        # print(df[EXPANDERS_VIEW])
        for index, row in df.iterrows():

            erk = row['erkenningsNummer']
            stands = row['plaatsen']
            pref = row['pref']
            merchant_branches = row['voorkeur.branches']
            maxi = row['voorkeur.maximum']

            valid_pref_stands = []
            for i, p in enumerate(pref):
                stand = self.positions_df.query(f"plaatsId == '{p}'")
                if len(stand) > 0:
                    stand_branches = self.get_branches_for_stand(p)
                    if len(stand_branches) == 0:
                        # no branched stand, allocate!
                        valid_pref_stands.append(p)
                    else:
                        # stand has branches, check compatible
                        branche_overlap = list(set(merchant_branches).intersection(set(stand_branches)))
                        if len(branche_overlap) > 0:
                            valid_pref_stands.append(p)
                if len(valid_pref_stands) == len(stands):
                    break

            if len(valid_pref_stands) < len(stands):
                stands_to_alloc = stands
            else:
                stands_to_alloc = valid_pref_stands

            self.market_output.add_allocation(erk, stands_to_alloc, self.merchant_object_by_id(erk))
            try:
                self.dequeue_marchant(erk)
            except KeyError as e:
                raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
            for st in stands:
                self.dequeue_market_stand(st)

        self.expanders_df = pd.concat([self.expanders_df, df])

    def allocation_phase_5(self):
        print("\n## Alle vpls's zijn ingedeeld we gaan de plaatsen die nog vrij zijn verdelen")
        print("\n--- FASE 5-a")
        print("nog open plaatsen: ", len(self.positions_df))
        print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

        # double check all vpls allocated
        df = self.merchants_df.query("status == 'vpl'")
        if len(df) == 0:
            print("check status OK all vpl's allocated.")
        else:
            print("check status ERROR not all vpl's allocated.")

        # make sure merchants are sorted
        self.merchants_df.sort_values(by=['sollicitatieNummer'], inplace=True, ascending=False)

        demand = self.merchants_df['voorkeur.maximum'].sum()
        available = len(self.positions_df)
        allocation_will_fit = demand <= available

        if allocation_will_fit:
            alist = self.merchants_df.query("alist == True & branche_required == 'yes'")
            print(alist[EXPANDERS_VIEW+["status"]])
            for index, row in alist.iterrows():
                erk = row['erkenningsNummer']
                pref = row['pref']
                merchant_branches = row['voorkeur.branches']
                maxi = row['voorkeur.maximum']
                mini = row['voorkeur.minimum']

                stands_available = self.get_stand_for_branche(merchant_branches[0])
                stands_available_list = stands_available['plaatsId'].to_list()

                if len(pref) == 0:
                    stds = self.cluster_finder.find_valid_cluster(stands_available_list, size=maxi, preferred=True)
                    if len(stds) == 0:
                        stds = self.cluster_finder.find_valid_cluster(stands_available_list, size=int(mini), preferred=True)
                    self.market_output.add_allocation(erk, stds, self.merchant_object_by_id(erk))
                    try:
                        self.dequeue_marchant(erk)
                    except KeyError as e:
                        raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
                    for st in stds:
                        self.dequeue_market_stand(st)
                else:
                    #all_prefs_available =  all(stand in pref[0:maxi] for stand in stands_available_list)
                    stds = self.cluster_finder.find_valid_cluster(pref, size=maxi, preferred=True)
                    if len(stds) == 0:
                        stds = self.cluster_finder.find_valid_cluster(pref, size=int(mini), preferred=True)
                    try:
                        self.dequeue_marchant(erk)
                    except KeyError as e:
                        raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
                    for st in stds:
                        self.dequeue_market_stand(st)

            print("\n--- FASE 5-b")
            print("Alist ingedeeld voor verplichte branches")
            print("nog open plaatsen: ", len(self.positions_df))
            print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

            alist_2 = self.merchants_df.query("alist == True & branche_required == 'no'")
            # print(alist_2[ALIST_VIEW])
            # print(alist_2[MERCHANTS_SORTED_VIEW])
            for index, row in alist_2.iterrows():
                erk = row['erkenningsNummer']
                pref = row['pref']
                merchant_branches = row['voorkeur.branches']
                maxi = row['voorkeur.maximum']
                mini = row['voorkeur.minimum']

                # cast prefs to actually vailable prefs
                res = self.positions_df['plaatsId'].isin(pref)
                pref = self.positions_df[res]['plaatsId'].to_list()

                stands_available = self.get_stand_for_branche(merchant_branches[0])
                stands_available_list = stands_available['plaatsId'].to_list()
                # print(erk, pref, maxi, mini, merchant_branches)
                # print(stands_available_list)

                if len(pref) == 0:
                    stds = stands_available_list[0:maxi]
                    self.market_output.add_allocation(erk, stds, self.merchant_object_by_id(erk))
                    try:
                        self.dequeue_marchant(erk)
                    except KeyError as e:
                        raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
                    for st in stds:
                        self.dequeue_market_stand(st)
                else:
                    all_prefs_available =  all(stand in pref for stand in stands_available_list)
                    if all_prefs_available:
                        stds = pref[0:maxi]
                        self.market_output.add_allocation(erk, stds, self.merchant_object_by_id(erk))
                        try:
                            self.dequeue_marchant(erk)
                        except KeyError as e:
                            raise MerchantDequeueError("Could not dequeue merchant, there may be a duplicate merchant id in the input data!")
                        for st in stds:
                            self.dequeue_market_stand(st)
                    else:
                        print("pref not available")
                        # TODD: what to do if not all pref are available
                        # create fixtures and test!
                        pass

            print("\n--- FASE 5-c")
            print("Alist ingedeeld voor NIET verplichte branches")
            print("nog open plaatsen: ", len(self.positions_df))
            print("ondenemers nog niet ingedeeld: ", len(self.merchants_df))

            blist = self.merchants_df.query("alist == False & branche_required == 'yes'")
            #print(blist[ALIST_VIEW])

            blist_2 = self.merchants_df.query("alist == False & branche_required == 'no'")
            #print(blist_2[ALIST_VIEW])

            #print(self.merchants_df)

        else:
            # TODO: allocation does not fit adjust strategy!
            # create proper testing fixtures
            pass

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

        self.allocation_phase_0()
        self.allocation_phase_1()
        self.allocation_phase_2()
        self.allocation_phase_3()
        #self.allocation_phase_4()
        #self.allocation_phase_5()

        if DEBUG:
            json_file = self.market_output.to_json_file()
            debug_redis = DebugRedisClient()
            debug_redis.insert_test_result(json_file)

        return {}


if __name__ == "__main__":
    from inputdata import FixtureDataprovider
    dp = FixtureDataprovider("../../fixtures/dapp_20211030/a_input.json")
    a = Allocator(dp)
    a.get_allocation()

