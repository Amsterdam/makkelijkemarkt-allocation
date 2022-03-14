import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import (
    alloc_erk,
    stands_erk,
    reject_erk,
    print_alloc,
    ErkenningsnummerNotFoudError,
)


class TestPrefOfOthersAllocation(unittest.TestCase):
    """
    Een ondernemer die aan de beurt is om ingedeeld
    te worden komt niet op een plek met de voorkeur van een
    ondenemer met een laag sollicitatieNummer
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=1,
            description="Frank Zappa",
            voorkeur={
                "anywhere": False,
                "branches": [],
                "maximum": 1,
                "minimum": 1,
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
            description="Moon Unit Zappa",
            voorkeur={
                "branches": [],
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
            sollicitatieNummer=3,
            description="Dweezil Zappa",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        dp.add_merchant(
            erkenningsNummer="4",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=4,
            description="Johan ten Broeke",
            voorkeur={
                "anywhere": False,
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page(["1", "2", "3", "4", "5", "6"])

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
        dp.add_stand(
            plaatsId="6",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)
        dp.add_rsvp(erkenningsNummer="4", attending=True)

        dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=1)
        dp.add_pref(erkenningsNummer="3", plaatsId="1", priority=1)
        dp.add_pref(erkenningsNummer="3", plaatsId="2", priority=1)
        dp.add_pref(erkenningsNummer="3", plaatsId="3", priority=1)
        dp.add_pref(erkenningsNummer="3", plaatsId="4", priority=1)
        dp.add_pref(erkenningsNummer="3", plaatsId="5", priority=1)
        dp.add_pref(erkenningsNummer="4", plaatsId="6", priority=1)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_assign_pref(self):
        """
        Case: erkenningsNummer 4 moet worden afgewezen omdat, op het moment dat erkenningsNummer 2
        wordt ingedeeld (geen voorkeur/anywhere) de voorkeursplek (6) de plek is met een voorkeur met het hoogste
        sollicitatienummer. Omdat erkenningeNummer 4 niet flexibel is volgt er een afwijzing.
        """
        afw = reject_erk("4", self.market_allocation)
        self.assertEqual(afw["erkenningsNummer"], "4")
