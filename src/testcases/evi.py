import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import print_alloc
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestEviMerchantNoRequiredBranche(unittest.TestCase):
    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_pref(erkenningsNummer="1", plaatsId="2", priority=1)

        # stands
        dp.add_page(["1", "2", "3", "99", "101", "103"])
        dp.add_stand(
            plaatsId="1",
            branches=["bogus"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.add_stand(plaatsId="2", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(
            plaatsId="3", branches=["101-agf"], properties=[], verkoopinrichting=[]
        )
        dp.add_stand(
            plaatsId="99",
            branches=["bogus"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.add_stand(plaatsId="100", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(
            plaatsId="101",
            branches=["bogus"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.add_stand(
            plaatsId="103",
            branches=["bogus"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )

        # branches
        dp.add_branche(brancheId="404-parfum", verplicht=False, maximumPlaatsen=3)
        dp.add_branche(brancheId="bogus", verplicht=False, maximumPlaatsen=3)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        self.dp = dp

    def test_allocation_combi_evi_no_required_branche(self):
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        # print_alloc(allocation)


class TestEVI(unittest.TestCase):
    """
    Een ondernemer met een EVI
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 2,
                "minimum": 2,
                "anywhere": True,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_pref(erkenningsNummer="1", plaatsId="2", priority=1)
        dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=2)

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="C Beefheart",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # stands
        dp.add_page(["1", "2", "3", "99", "100", "101", "103"])
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.add_stand(plaatsId="2", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(
            plaatsId="3", branches=["101-agf"], properties=[], verkoopinrichting=[]
        )
        dp.add_stand(
            plaatsId="99",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.add_stand(plaatsId="100", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(
            plaatsId="101",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.add_stand(
            plaatsId="103",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=False, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        self.dp = dp

    def test_can_only_be_at_evi_stand(self):
        """
        kan enkel op een EVI plaats staan
        """
        self.dp.mock()
        allocator = Allocator(self.dp)
        self.market_allocation = allocator.get_allocation()
        # 101, 103 are evi stands. Zappa prefs are 2, 3 (assign evi anyway)
        erk = alloc_erk("1", self.market_allocation)
        a = [a in erk["plaatsen"] for a in ["101", "103"]]
        self.assertTrue(a)

    def test_most_suitable_stand(self):
        """
        komt op de meest geschikte EVI plaats te staan
        """
        # Branche overlap is hier belangrijker dan de prioritering van de ondernemer.

        self.dp.add_merchant(
            erkenningsNummer="55",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Ornette Coleman",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_rsvp(erkenningsNummer="55", attending=True)
        self.dp.add_pref(erkenningsNummer="55", plaatsId="99", priority=1)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        twz = alloc_erk("55", allocation)
        self.assertListEqual(twz["plaatsen"], ["99"])

    def test_can_not_expand_to_non_evi_stand(self):
        """
        kan niet uitbreiden naar een niet-EVI plaats
        """
        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="C Beefheart",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 2,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_pref(erkenningsNummer="2", plaatsId="1", priority=1)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=2)

        self.dp.mock()
        allocator = Allocator(self.dp)
        self.market_allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("2", self.market_allocation)["plaatsen"], ["1"])

    def test_reject_if_no_more_evi_stands(self):
        """
        wordt afgewezen als er geen EVI plaatsen meer beschikbaar zijn
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_pref(erkenningsNummer="1", plaatsId="1", priority=1)

        # stands
        dp.add_page(["1"])
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.mock()
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        self.assertListEqual(market_allocation["toewijzingen"], [])
        self.assertEqual(len(market_allocation["afwijzingen"]), 1)

    def test_pref_to_moving_vpl(self):
        """
        krijgt voorrang boven VPLs die willen verplaatsen
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="3",
            description="Jopie Goedkoopie",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_pref(erkenningsNummer="1", plaatsId="2", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=1)

        # stands
        dp.add_page(["1", "2"])
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.mock()
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("2", market_allocation)["plaatsen"], ["1"])
        self.assertListEqual(alloc_erk("1", market_allocation)["plaatsen"], ["2"])

    def test_pref_to_soll_no_evi(self):
        """
        krijgt voorrang boven sollicitanten zonder EVI
        """
        # Altijd eerst EVI plaatsen proberen vullen met EVI ondernemers.
        # Ook indien `strategy === 'conservative'`.
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="3",
            description="Jopie Goedkoopie",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 1,
                "minimum": 1,
                "anywhere": True,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_pref(erkenningsNummer="1", plaatsId="2", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=1)

        # stands
        dp.add_page(["1", "2"])
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        dp.mock()
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("1", market_allocation)["plaatsen"], ["2"])
        self.assertEqual(len(market_allocation["afwijzingen"]), 0)
