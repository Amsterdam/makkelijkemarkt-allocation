import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestVPLExpansionPrio(unittest.TestCase):
    """
    Een VPL die wil verplaatsen
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": [],
                "maximum": 3,
                "minimum": 1,
                "anywhere": False,
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
            description="c beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "anywhere": True,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=0)

        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        dp.set_alist([{"erkenningsNummer": "2"}])

        dp.add_page(["1", "2", "3", "4", "5"])

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
        dp.add_stand(
            plaatsId="5",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )

        self.dp = dp

    def test_vpl_gets_max_expansions(self):
        """
        uitbreiden vpl gaat voor plaatsen soll
        """
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        stands = stands_erk("1", allocation)
        self.assertSetEqual(set(stands), {"1", "2", "3"})

    def test_eb_gets_prio_over_soll(self):
        """
        uitbreidende eb gaat voor plaatsen soll
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["3"],
            status="eb",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="2", priority=0)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        stands = stands_erk("1", allocation)

        # EB wordt uitgebreid daar de voorkeursplek
        self.assertSetEqual({"2", "3"}, set(stands))

    def test_vpl_verplaatsen_gaat_na_vaste_vpl(self):
        """
        static vpl gaat voor verplaatsende vpl
        """
        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["4"],
            status="vpl",
            sollicitatieNummer="2",
            description="vpl verplaatser",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=0)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        stands_1 = stands_erk("1", allocation)
        stands_2 = stands_erk("2", allocation)

        # Non moving VPL has prio, so they get 3 places
        self.assertSetEqual({"1", "2", "3"}, set(stands_1))
        # Moving VPL has no prio so they get remaining 2 places
        self.assertSetEqual({"4", "5"}, set(stands_2))

    def test_vpl_uitbreiden_niet_over_mercato_verplaatser(self):
        """
        static vpl gaat voor verplaatsende vpl
        """
        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["3"],
            status="vpl",
            sollicitatieNummer="2",
            description="vpl verplaatser",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=["5"],
            status="vpl",
            sollicitatieNummer="3",
            description="vpl blokkade",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_pref(erkenningsNummer="2", plaatsId="5", priority=0)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        stands_1 = stands_erk("1", allocation)
        stands_2 = stands_erk("2", allocation)
        stands_3 = stands_erk("3", allocation)
        self.assertSetEqual(set(stands_1), {"1", "2"})
        self.assertSetEqual(set(stands_2), {"3"})
        self.assertSetEqual(set(stands_3), {"4", "5"})

    def test_vpl_uitbreiden_niet_over_mercato_verplaatser(self):
        """
        static vpl gaat voor verplaatsende vpl
        """
        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["2"],
            status="vpl",
            sollicitatieNummer="2",
            description="vpl verplaatser",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=["4"],
            status="vpl",
            sollicitatieNummer="3",
            description="vpl blokkade",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        # self.dp.add_merchant(
        #     erkenningsNummer="4",
        #     plaatsen=["5"],
        #     status="vpl",
        #     sollicitatieNummer="4",
        #     description="vpl",
        #     voorkeur={
        #         "branches": [],
        #         "maximum": 2,
        #         "minimum": 1,
        #         "anywhere": False,
        #         "verkoopinrichting": [],
        #         "absentFrom": "",
        #         "absentUntil": "",
        #     },
        # )

        self.dp.add_pref(erkenningsNummer="2", plaatsId="4", priority=0)
        self.dp.add_pref(erkenningsNummer="3", plaatsId="5", priority=0)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        stands_1 = stands_erk("1", allocation)
        stands_2 = stands_erk("2", allocation)
        stands_3 = stands_erk("3", allocation)
        self.assertSetEqual(set(stands_1), {"1", "2"})
        self.assertSetEqual(set(stands_2), {"3"})
        self.assertSetEqual(set(stands_3), {"4", "5"})

    def test_vpl_verplaatsende_plekken_reserved(self):
        """
        static vpl gaat voor verplaatsende vpl
        """
        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["2"],
            status="vpl",
            sollicitatieNummer="2",
            description="vpl verplaatser",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=["4"],
            status="vpl",
            sollicitatieNummer="3",
            description="vpl blokkade",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="4",
            plaatsen=["5"],
            status="vpl",
            sollicitatieNummer="4",
            description="vpl",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_pref(erkenningsNummer="2", plaatsId="4", priority=0)
        self.dp.add_pref(erkenningsNummer="3", plaatsId="5", priority=0)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        stands_1 = stands_erk("1", allocation)
        stands_2 = stands_erk("2", allocation)
        stands_3 = stands_erk("3", allocation)
        self.assertSetEqual(set(stands_1), {"1", "2"})
        self.assertSetEqual(set(stands_2), {"3"})
        self.assertSetEqual(set(stands_3), {"4", "5"})
