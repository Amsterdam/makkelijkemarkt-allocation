from socket import ALG_OP_DECRYPT
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

        # merchants
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

        allocs = allocation["toewijzingen"]
        stands = allocs[0]["plaatsen"]
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
        # EB wil uitbreiden naar plek 2, conflict met sollicitant
        self.dp.add_pref(erkenningsNummer="1", plaatsId="2", priority=0)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        toewijzingen = allocation["toewijzingen"]
        stands = get_toew_by_erk(toewijzingen, "1")["plaatsen"]

        self.assertEqual(2, len(stands))
        self.assertIn("2", stands)

    def test_vpl_verplaatsen_gaat(self):
        """
        uitbreidende eb gaat voor plaatsen soll
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
        # EB wil uitbreiden naar plek 2, conflict met sollicitant
        self.dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=0)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        toewijzingen = allocation["toewijzingen"]
        stands_1 = get_toew_by_erk(toewijzingen, "1")["plaatsen"]
        stands_2 = get_toew_by_erk(toewijzingen, "2")["plaatsen"]

        self.assertEqual(2, len(stands_1))
        self.assertEqual(2, len(stands_2))
        self.assertSetEqual({"1", "2"}, set(stands_1))
        self.assertSetEqual({"3", "4"}, set(stands_2))


def get_toew_by_erk(toewijzingen, erkenningsnummer):
    return list(
        filter(
            lambda toew: toew["ondernemer"]["erkenningsNummer"]
            == str(erkenningsnummer),
            toewijzingen,
        )
    )[0]
