import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestTVPallocation(unittest.TestCase):
    """
    Een VPL/TVPL die ingedeeld wil worden
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-afg"],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="C Beefheart",
            voorkeur={
                "branches": ["101-afg"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="3",
            description="J Medeski",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # stands
        dp.add_page(["1", "2"])
        dp.add_stand(
            plaatsId="1", branches=[], properties=["boom"], verkoopinrichting=[]
        )
        dp.add_stand(
            plaatsId="2", branches=[], properties=["boom"], verkoopinrichting=[]
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_pref_vpl_to_soll(self):
        """
        krijgt voorkeur boven sollicitanten
        """
        stands = self.market_allocation["toewijzingen"]
        self.assertEqual(len(stands), 1)

    def test_allocation_fixed_stands(self):
        """
        wordt toegewezen aan zijn vaste plaats(en)
        """
        # Dit scenario laat expres 1 plaats vrij om een regression bug
        # in `calcSizes` te voorkomen (`size` werd daar verkeerd
        # berekend als er meer dan genoeg plaatsen waren).
        allocs = self.market_allocation["toewijzingen"]
        stands = allocs[0]["plaatsen"]
        self.assertListEqual(stands, ["1", "2"])

    def test_vpl_max_stands(self):
        """
        kan zijn aantal vaste plaatsen verkleinen door een maximum in te stellen
        """
        self.dp.add_merchant(
            erkenningsNummer="4",
            plaatsen=["3", "4"],
            status="vpl",
            sollicitatieNummer="4",
            description="Tony Alva",
            voorkeur={
                "branches": ["666-heavy-metal"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_page(["3", "4"])
        self.dp.add_stand(
            plaatsId="3", branches=[], properties=[], verkoopinrichting=[]
        )
        self.dp.add_stand(
            plaatsId="4", branches=[], properties=[], verkoopinrichting=[]
        )

        self.dp.mock()
        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        twz = alloc_erk("4", market_allocation)
        num_stands = len(twz["plaatsen"])
        self.assertEqual(num_stands, 1)

    def test_vpl_fixed_not_available(self):
        """
        wordt afgewezen als zijn vaste plaatsen niet beschikbaar zijn
        """
        self.dp.add_merchant(
            erkenningsNummer="4",
            plaatsen=["7", "9"],
            status="vpl",
            sollicitatieNummer="4",
            description="Tony Alva",
            voorkeur={
                "branches": ["101-afg"],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        self.assertTrue(len(market_allocation["afwijzingen"]) == 3)
        self.assertEqual(reject_erk("4", market_allocation)["reason"]["code"], 5)

    @unittest.skip(
        "Uitgezet, omdat nog niet besloten is hoe om te gaan met 'willekeurig indelen' voor VPL."
    )
    def test_other_stands_if_not_available(self):
        """
        kan hetzelfde aantal willekeurige plaatsen krijgen als zijn eigen plaatsen niet beschikbaar zijn
        """
        self.assertTrue(False)


class TestTVPLZallocation(unittest.TestCase):
    """
    Een TVPLZ die ingedeeld wil worden
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-afg"],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="tvplz",
            sollicitatieNummer="1",
            description="C Beefheart",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="3",
            description="J Medeski",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # stands
        dp.add_page(["1", "2", "3"])
        dp.add_stand(plaatsId="1", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId="2", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(
            plaatsId="3", branches=["101-agf"], properties=[], verkoopinrichting=[]
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_tvplz_must_register(self):
        """
        moet zich eerst expliciet aanmelden
        """
        twz = alloc_erk("3", self.market_allocation)
        self.assertEqual(twz["plaatsen"], ["3"])
        self.assertEqual(
            twz["ondernemer"]["description"],
            "J Medeski",
        )

        self.dp.add_rsvp(erkenningsNummer="2", attending=True)
        self.dp.mock()

        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        twz = alloc_erk("2", allocation)
        self.assertListEqual(twz["plaatsen"], ["3"])
        self.assertEqual(twz["ondernemer"]["description"], "C Beefheart")

    def test_pref_to_soll(self):
        """
        krijgt voorkeur boven sollicitanten
        """
        twz = alloc_erk("3", self.market_allocation)
        self.assertEqual(twz["plaatsen"], ["3"])
        self.assertEqual(
            twz["ondernemer"]["description"],
            "J Medeski",
        )

        self.dp.add_rsvp(erkenningsNummer="2", attending=True)
        self.dp.mock()

        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        twz = alloc_erk("2", allocation)
        rejection = reject_erk("3", allocation)
        self.assertListEqual(twz["plaatsen"], ["3"])
        self.assertEqual(twz["ondernemer"]["description"], "C Beefheart")
        self.assertEqual(rejection["ondernemer"]["description"], "J Medeski")

    def test_non_pref_to_evi_and_branche(self):
        """
        heeft geen voorrang over verplichte branche- en EVI ondernemers
        """
        self.dp.add_merchant(
            erkenningsNummer="18",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="34",
            description="D Moon",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_rsvp(erkenningsNummer="2", attending=True)
        self.dp.add_rsvp(erkenningsNummer="18", attending=True)
        self.dp.mock()

        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertEqual(
            alloc_erk("18", allocation)["ondernemer"]["description"], "D Moon"
        )
        self.assertEqual(
            reject_erk("2", allocation)["ondernemer"]["description"], "C Beefheart"
        )

    def test_right_to_number_of_stands(self):
        """
        heeft recht op een vast aantal plaatsen, maar heeft geen vaste plaats(en)
        """
        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="tvplz",
            sollicitatieNummer="1",
            description="C Beefheart",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        self.dp.add_page(["6", "7", "8"])
        self.dp.add_stand(
            plaatsId="6", branches=[], properties=[], verkoopinrichting=[]
        )
        self.dp.add_stand(
            plaatsId="7", branches=[], properties=[], verkoopinrichting=[]
        )
        self.dp.add_stand(
            plaatsId="8", branches=[], properties=[], verkoopinrichting=[]
        )

        self.dp.mock()

        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("2", allocation)["plaatsen"], ["6", "7"])
        self.assertEqual(
            alloc_erk("2", allocation)["ondernemer"]["description"], "C Beefheart"
        )

    @unittest.skip("Navraag markten")
    def test_can_not_limit_stands(self):
        """
        mag zijn vaste aantal plaatsen niet verkleinen
        """
        self.assertTrue(False)

    @unittest.skip("Dit is de default, navraag markten")
    def test_can_expand_stands(self):
        """
        mag zijn vaste aantal plaatsen uitbreiden indien mogelijk
        """
        self.assertTrue(False)
