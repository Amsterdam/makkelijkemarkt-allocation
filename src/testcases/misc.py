import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc
from kjk.test_utils import ErkenningsnummerNotFoudError


class TestRejections(unittest.TestCase):
    """
    Een ondernemer wordt afgewezen
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
                "branches": [],
                "maximum": 4,
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
            sollicitatieNummer="12",
            description="C Beefheart",
            voorkeur={
                "branches": ["101-bbb"],
                "maximum": 3,
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

        dp.add_page([None, "1", "2", None])

        # stands
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
            verkoopinrichting=[],
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_market_full_rejection(self):
        """
        als de markt vol is
        """
        self.assertEqual(len(self.market_allocation["afwijzingen"]), 2)


class TestVPLcancellation(unittest.TestCase):
    """
    Een VPL/TVPL die niet ingedeeld wil worden
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
                "branches": [],
                "maximum": 4,
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
            sollicitatieNummer="12",
            description="C Beefheart",
            voorkeur={
                "branches": ["101-bbb"],
                "maximum": 3,
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

        dp.add_page([None, "1", "2", None])

        # stands
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
            verkoopinrichting=[],
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=False)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_cancellation(self):
        """
        kan zich afmelden voor een marktdag
        """
        with self.assertRaises(ErkenningsnummerNotFoudError):
            alloc_erk("1", self.market_allocation)
        with self.assertRaises(ErkenningsnummerNotFoudError):
            reject_erk("1", self.market_allocation)

    def test_periodic_cancellation(self):
        """
        kan zijn aanwezigheid voor een bepaalde periode uitschakelen
        """
        self.dp.add_merchant(
            erkenningsNummer="6",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="3",
            description="John Rambo",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
                # "absentFrom": "2021-10-20",
                # "absentUntil": "2021-11-20",
            },
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("6", allocation)["plaatsen"], ["1"])

        self.dp.update_merchant(
            erkenningsNummer="6",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="3",
            description="John Rambo",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "2021-10-20",
                "absentUntil": "2021-11-20",
            },
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        with self.assertRaises(ErkenningsnummerNotFoudError):
            alloc_erk("6", self.market_allocation)
        with self.assertRaises(ErkenningsnummerNotFoudError):
            reject_erk("6", self.market_allocation)


class TestTVPLcancellation(unittest.TestCase):
    """
    Een TVPLZ die niet ingedeeld wil worden
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="tvplz",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 4,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Dweezil Zappa",
            voorkeur={
                "branches": [],
                "maximum": 4,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page([None, "1", "2", None])

        # stands
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
            verkoopinrichting=[],
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_register_tvpl(self):
        """
        hoeft zich niet af te melden als zij zichzelf niet aangemeld hebben
        """
        with self.assertRaises(ErkenningsnummerNotFoudError):
            alloc_erk("1", self.market_allocation)
        with self.assertRaises(ErkenningsnummerNotFoudError):
            reject_erk("1", self.market_allocation)


class Test_SOLL_EXP_EXPF(unittest.TestCase):
    """
    Een sollicitant met een tijdelijke vaste plaats (exp of expf)
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="exp",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 4,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Dweezil Zappa",
            voorkeur={
                "branches": [],
                "maximum": 4,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page([None, "1", "2", None])

        # stands
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
            verkoopinrichting=[],
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_must_register(self):
        """
        moet zich aanmelden als aanwezig om ingedeeld te worden
        """
        with self.assertRaises(ErkenningsnummerNotFoudError):
            alloc_erk("1", self.market_allocation)
        with self.assertRaises(ErkenningsnummerNotFoudError):
            reject_erk("1", self.market_allocation)

    def test_allocated_before_other_soll(self):
        """
        wordt ingedeeld voor andere sollicitanten
        """
        self.dp.add_rsvp(erkenningsNummer="1", attending=True)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["1", "2"])

    def test_can_not_move_if_fixed_stand(self):
        """
        kan niet verplaatsen als zij een vaste plaats hebben
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="exp",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_rsvp(erkenningsNummer="1", attending=True)

        self.dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        self.dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=1)
        self.dp.add_page([None, "3", "4", None])

        # stands
        self.dp.add_stand(
            plaatsId="3",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_stand(
            plaatsId="4",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["1", "2"])

    def test_can_not_have_min_pref(self):
        """
        kan geen minimum gewenste plaatsen opgeven in hun voorkeuren
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="exp",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 6,
                "minimum": 4,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_rsvp(erkenningsNummer="1", attending=True)

        self.dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        self.dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=1)
        self.dp.add_page([None, "3", "4", None])

        # stands
        self.dp.add_stand(
            plaatsId="3",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_stand(
            plaatsId="4",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["1", "2"])

    def test_can_not_have_max_pref(self):
        """
        kan geen maximum aantal gewenste plaatsen opgeven in hun voorkeuren
        """
        dp = MockDataprovider("../fixtures/test_input.json")
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="exp",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 3,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_rsvp(erkenningsNummer="1", attending=True)

        dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=1)
        dp.add_page([None, "1", "2", "3", "4", None])

        # stands
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
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="4",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["1", "2"])


class TestMinimizeRejections(unittest.TestCase):
    """
    Minimaliseer het aantal afwijzingen
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=1,
            description="Frank Zappa",
            voorkeur={
                "branches": [],
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
            sollicitatieNummer=2,
            description="Ton Waits",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=3,
            description="Frank London",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        dp.add_pref(erkenningsNummer="1", plaatsId="1", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="3", priority=1)
        dp.add_page([None, "1", "2", "3", None])

        # stands
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
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp = dp

    def test_competing_min_pref(self):
        """
        bij concurrerende minimum voorkeuren
        """
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        num_rejects = len(allocation["afwijzingen"])
        self.assertEqual(num_rejects, 2)
        erk = alloc_erk("1", allocation)
        erk["plaatsen"].sort()
        a = ["1", "2"]
        a.sort()
        self.assertListEqual(erk["plaatsen"], a)

    def test_rejection_for_branches(self):
        """
        bij de 2de verplichte branche ondernemer als de 1ste wordt afgewezen
        """
        self.dp = MockDataprovider("../fixtures/test_input.json")
        self.dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-goederen"],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="1",
            description="Tom Waits",
            voorkeur={
                "branches": ["101-goederen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_rsvp(erkenningsNummer="1", attending=True)
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)
        self.dp.add_page([None, "4", None])
        self.dp.add_branche(brancheId="101-goederen", verplicht=True, maximumPlaatsen=1)
        self.dp.add_stand(
            plaatsId="4",
            branches=["101-goederen"],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("2", allocation)
        self.assertListEqual(erk["plaatsen"], ["4"])
