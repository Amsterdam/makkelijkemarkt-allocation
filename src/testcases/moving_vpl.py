import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestMovingVPL(unittest.TestCase):
    """
    Een VPL die wil verplaatsen
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="1",
            description="frank zappa",
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
            plaatsen=["3"],
            status="vpl",
            sollicitatieNummer="2",
            description="c beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page([None, "1", "2", "3", "4", "5", None])

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

    def test_can_move_free_stand(self):
        """
        kan altijd verplaatsen naar een losse plaats
        """
        self.dp.add_pref(erkenningsNummer="2", plaatsId="5", priority=1)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("2", allocation)
        self.assertListEqual(erk["plaatsen"], ["5"])

    def test_can_not_take_other_vpl_stand(self):
        """
        mag niet naar een plaats van een andere aanwezige VPL
        """
        self.dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=1)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("2", allocation)
        self.assertListEqual(erk["plaatsen"], ["3"])

    def test_can_switch_stands(self):
        """
        mag ruilen met een andere VPL
        """
        self.dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        self.dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=2)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="1", priority=1)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        erk_2 = alloc_erk("2", allocation)
        self.assertListEqual(erk["plaatsen"], ["3", "4"])
        self.assertListEqual(erk_2["plaatsen"], ["1"])

    def test_can_switch_stands_2(self):
        """
        mag ruilen met een andere VPL
        """
        self.dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=["5"],
            status="vpl",
            sollicitatieNummer="1",
            description="John Coltrane",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        self.dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=2)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="5", priority=1)
        self.dp.add_pref(erkenningsNummer="3", plaatsId="1", priority=1)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        erk_2 = alloc_erk("2", allocation)
        erk_3 = alloc_erk("3", allocation)
        self.assertListEqual(erk["plaatsen"], ["3", "4"])
        self.assertListEqual(erk_2["plaatsen"], ["5"])
        self.assertListEqual(erk_3["plaatsen"], ["1"])

    def test_can_switch_stands_3(self):
        """
        mag ruilen met een andere VPL
        """
        self.dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=["5"],
            status="vpl",
            sollicitatieNummer="3",
            description="John Coltrane",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        self.dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=2)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="5", priority=1)
        self.dp.add_pref(erkenningsNummer="3", plaatsId="3", priority=1)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        erk_2 = alloc_erk("2", allocation)
        erk_3 = alloc_erk("3", allocation)
        self.assertListEqual(erk["plaatsen"], ["1", "2"])
        self.assertListEqual(erk_2["plaatsen"], ["5"])
        self.assertListEqual(erk_3["plaatsen"], ["3"])

    def test_will_not_move_if_better_moving_vpl(self):
        """
        blijft staan als een VPL met hogere ancienniteit dezelfde voorkeur heeft
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["3"],
            status="vpl",
            sollicitatieNummer="2",
            description="c beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="5", priority=1)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="5", priority=1)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["5"])

    def test_can_move_to_stand_based_on_one_pref(self):
        """
        kan naar een locatie met minimaal 1 beschikbare voorkeur
        """
        self.dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=1)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("2", allocation)
        self.assertListEqual(erk["plaatsen"], ["3"])

    def test_keep_number_of_stand(self):
        """
        met meerdere plaatsen behoudt dit aantal na verplaatsing
        """
        self.dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        self.dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=2)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["4", "5"])
        self.assertEqual(len(erk["plaatsen"]), len(erk["ondernemer"]["plaatsen"]))

    def test_keep_stands_if_prefs_not_available(self):
        """
        raken hun eigen plaats niet kwijt als hun voorkeur niet beschikbaar is
        """
        self.dp.add_pref(erkenningsNummer="1", plaatsId="8", priority=1)
        self.dp.add_pref(erkenningsNummer="1", plaatsId="9", priority=2)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["1", "2"])
        self.assertEqual(len(erk["plaatsen"]), len(erk["ondernemer"]["plaatsen"]))

        # spot 3 is taken by other vpl
        self.dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["1", "2"])
        self.assertEqual(len(erk["plaatsen"]), len(erk["ondernemer"]["plaatsen"]))

    def test_no_pref_to_evi(self):
        """krijgt GEEN voorrang boven EVI ondernemers"""
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="c beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="9", priority=1)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="9", priority=1)

        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=1)

        self.dp.add_page([None, "9", None])
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        # stands
        self.dp.add_stand(
            plaatsId="9",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("2", allocation)
        self.assertListEqual(erk["plaatsen"], ["9"])

    def test_pref_to_evi_if_evi(self):
        """
        krijgt WEL voorrang boven EVI ondernemers als zij zelf ook een EVI hebben
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["3"],
            status="soll",
            sollicitatieNummer="2",
            description="c beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="9", priority=1)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="9", priority=1)

        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=1)

        self.dp.add_page([None, "9", None])
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        # stands
        self.dp.add_stand(
            plaatsId="9",
            branches=["bak"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["9"])

    def test_pref_to_bak_if_baking(self):
        """
        krijgt WEL voorrang boven bak ondernemers als zij zelf ook bakken
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": ["bak"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["3"],
            status="soll",
            sollicitatieNummer="2",
            description="c beefheart",
            voorkeur={
                "branches": ["bak"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="9", priority=1)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="9", priority=1)

        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=1)

        self.dp.add_page([None, "9", None])
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        # stands
        self.dp.add_stand(
            plaatsId="9",
            branches=["bak"],
            properties=[],
            verkoopinrichting=[],
        )

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["9"])

    def test_pref_to_non_baking(self):
        """
        krijgt WEL voorrang boven sollicitanten die niet willen bakken
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.update_merchant(
            erkenningsNummer="2",
            plaatsen=["3"],
            status="soll",
            sollicitatieNummer="2",
            description="c beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_pref(erkenningsNummer="1", plaatsId="9", priority=1)
        self.dp.add_pref(erkenningsNummer="2", plaatsId="9", priority=1)

        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=1)

        self.dp.add_page([None, "9", None])
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        # stands
        self.dp.add_stand(
            plaatsId="9",
            branches=["bak"],
            properties=[],
            verkoopinrichting=[],
        )

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("1", allocation)
        self.assertListEqual(erk["plaatsen"], ["9"])
