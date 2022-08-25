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

        dp.add_page(["1", "2", "3"])

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

    def test_vpl_gets_max_expansions(self):
        """
        kan altijd verplaatsen naar een losse plaats
        """
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        allocs = allocation["toewijzingen"]
        stands = allocs[0]["plaatsen"]
        self.assertSetEqual(set(stands), {"1", "2", "3"})
