import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider

class TestTVPallocation(unittest.TestCase):
    """
    Een VPL/TVPL die ingedeeld wil worden    
    """
    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(erkenningsNummer='1',
                        plaatsen=['1', '2'],
                        status='vpl',
                        sollicitatieNummer="2",
                        description='Frank Zappa',
                        voorkeur={"branches": ['101-afg'], "maximum": 2, "minimum": 2, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        dp.add_merchant(erkenningsNummer='2',
                        plaatsen=[],
                        status='soll',
                        sollicitatieNummer="2",
                        description='C Beefheart',
                        voorkeur={"branches": ['101-afg'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        dp.add_merchant(erkenningsNummer='3',
                        plaatsen=[],
                        status='soll',
                        sollicitatieNummer="3",
                        description='J Medeski',
                        voorkeur={"branches": ['mooie spullen'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        # stands
        dp.add_page(['1', '2'])
        dp.add_stand(plaatsId='1', branches=[], properties=['boom'], verkoopinrichting=[])
        dp.add_stand(plaatsId='2', branches=[], properties=['boom'], verkoopinrichting=[])

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer='2', attending=True)
        dp.add_rsvp(erkenningsNummer='3', attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_pref_vpl_to_soll(self):
        """
        krijgt voorkeur boven sollicitanten
        """
        stands = self.market_allocation['toewijzingen']
        self.assertEqual(len(stands), 1)

    def test_allocation_fixed_stands(self):
        """
        wordt toegewezen aan zijn vaste plaats(en)
        """
        # Dit scenario laat expres 1 plaats vrij om een regression bug
        # in `calcSizes` te voorkomen (`size` werd daar verkeerd
        # berekend als er meer dan genoeg plaatsen waren).
        allocs= self.market_allocation['toewijzingen']
        stands = allocs[0]['plaatsen']
        self.assertListEqual(stands, ['1', '2'])

    @unittest.skip("Navragen bij markt bureau, krimpen zonder voorkeuren?")
    def test_vpl_max_stands(self):
        """
        kan zijn aantal vaste plaatsen verkleinen door een maximum in te stellen
        """
        self.dp.add_merchant(erkenningsNummer='4',
                             plaatsen=['3', '4'],
                             status='vpl',
                             sollicitatieNummer="4",
                             description='Tony Alva',
                             voorkeur={"branches": ['666-heavy-metal'], "maximum": 1, "minimum": 1,
                                       "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        self.dp.add_page(['3', '4'])
        self.dp.add_stand(plaatsId='3', branches=[], properties=[], verkoopinrichting=[])
        self.dp.add_stand(plaatsId='4', branches=[], properties=[], verkoopinrichting=[])

        self.dp.mock()
        allocator = Allocator(self.dp)
        market_allocation = allocation = allocator.get_allocation()
        num_stands = len(market_allocation['toewijzingen'][0]['plaatsen'])
        self.assertEqual(num_stands, 1)

    def test_vpl_fixed_not_available(self):
        """
        wordt afgewezen als zijn vaste plaatsen niet beschikbaar zijn
        """
        self.dp.add_merchant(erkenningsNummer='4',
                             plaatsen=['7', '9'],
                             status='vpl',
                             sollicitatieNummer="4",
                             description='Tony Alva',
                             voorkeur={"branches": ['101-afg'], "maximum": 2, "minimum": 2, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})
        self.dp.mock()
        allocator = Allocator(self.dp)
        market_allocation = allocation = allocator.get_allocation()
        self.assertTrue(len(market_allocation['afwijzingen']) == 1)
        self.assertEqual(market_allocation['afwijzingen'][0]['reason']['code'],  5)

    @unittest.skip("Uitgezet, omdat nog niet besloten is hoe om te gaan met 'willekeurig indelen' voor VPL.")
    def test_other_stands_if_not_available(self):
        """
        kan hetzelfde aantal willekeurige plaatsen krijgen als zijn eigen plaatsen niet beschikbaar zijn
        """
        pass


class TestTVPLZallocation(unittest.TestCase):
    """
    Een TVPLZ die ingedeeld wil worden
    """
    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(erkenningsNummer='1',
                        plaatsen=['1', '2'],
                        status='vpl',
                        sollicitatieNummer="2",
                        description='Frank Zappa',
                        voorkeur={"branches": ['101-afg'], "maximum": 2, "minimum": 2, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        dp.add_merchant(erkenningsNummer='2',
                        plaatsen=[],
                        status='tvplz',
                        sollicitatieNummer="1",
                        description='C Beefheart',
                        voorkeur={"branches": ['mooie spullen'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        dp.add_merchant(erkenningsNummer='3',
                        plaatsen=[],
                        status='soll',
                        sollicitatieNummer="3",
                        description='J Medeski',
                        voorkeur={"branches": ['mooie spullen'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        # stands
        dp.add_page(['1', '2', '3'])
        dp.add_stand(plaatsId='1', branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId='2', branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId='3', branches=[], properties=[], verkoopinrichting=[])

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer='3', attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_tvplz_must_register(self):
        """
        moet zich eerst expliciet aanmelden
        """

        self.assertEqual(self.market_allocation['toewijzingen'][1]['plaatsen'], ['3'])
        self.assertEqual(self.market_allocation['toewijzingen'][1]['ondernemer']['description'], "J Medeski")

        self.dp.add_rsvp(erkenningsNummer='2', attending=True)
        self.dp.mock()

        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(allocation['toewijzingen'][1]['plaatsen'], ['3'])
        self.assertEqual(allocation['toewijzingen'][1]['ondernemer']['description'], "C Beefheart")

    def test_pref_to_soll(self):
        """
        krijgt voorkeur boven sollicitanten
        """
        self.assertEqual(self.market_allocation['toewijzingen'][1]['plaatsen'], ['3'])
        self.assertEqual(self.market_allocation['toewijzingen'][1]['ondernemer']['description'], "J Medeski")

        self.dp.add_rsvp(erkenningsNummer='2', attending=True)
        self.dp.mock()

        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(allocation['toewijzingen'][1]['plaatsen'], ['3'])
        self.assertEqual(allocation['toewijzingen'][1]['ondernemer']['description'], "C Beefheart")
        self.assertEqual(allocation['afwijzingen'][0]['ondernemer']['description'], "J Medeski")

    def test_non_pref_to_evi_and_brache(self):
        """
        heeft geen voorrang over verplichte branche- en EVI ondernemers
        """
        pass

    def test_right_to_number_of_stands(self):
        """
        heeft recht op een vast aantal plaatsen, maar heeft geen vaste plaats(en)
        """
        pass

    def test_can_not_limit_stands(self):
        """
        mag zijn vaste aantal plaatsen niet verkleinen
        """
        pass

    def test_can_expand_stands(self):
        """
        mag zijn vaste aantal plaatsen uitbreiden indien mogelijk
        """
        pass
