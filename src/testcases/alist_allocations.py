import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestAlistAllocations(unittest.TestCase):
    """
    Een sollicitant op de A-lijst
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
            sollicitatieNummer="2",
            description="C Beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page([None, "1", None])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        self.dp = dp

    def test_assign_pref_to_blist_evi_and_baking(self):
        """
        krijgt WEL voorrang over EVI- en verplichte branche sollicitanten op de B-lijst
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
                "branches": [],
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
            sollicitatieNummer="2",
            description="C Beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page([None, "1", None])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        dp.set_alist([{"erkenningsNummer": "2"}])

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        erk = alloc_erk("2", allocation)
        self.assertListEqual(erk["plaatsen"], ["1"])

    def test_assign_pref_to_blist(self):
        """
        krijgt voorrang over gelijkwaardige sollicitanten op de B-lijst
        """
        # normally erk 1 get the stand
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        res = alloc_erk("1", allocation)
        self.assertListEqual(res["plaatsen"], ["1"])

        # put 2 on the alist and retry
        self.dp.set_alist([{"erkenningsNummer": "2"}])

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        res = alloc_erk("2", allocation)
        self.assertListEqual(res["plaatsen"], ["1"])

    def test_expansion_pref_to_blist(self):
        """
        mag maximaal uitbreiden voordat B-lijst ondernemers mogen uitbreiden
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=1,
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": True,
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
            description="C Beefheart",
            voorkeur={
                "branches": [],
                "anywhere": True,
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
            sollicitatieNummer=3,
            description="Ornette",
            voorkeur={
                "branches": [],
                "maximum": 2,
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

        dp.add_pref(erkenningsNummer="1", plaatsId="1", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="3", priority=1)
        dp.add_pref(erkenningsNummer="3", plaatsId="4", priority=1)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        res_zappa = alloc_erk("1", allocation)
        res_beefheart = alloc_erk("2", allocation)

        self.assertEqual(len(res_zappa["plaatsen"]), 2)
        self.assertEqual(len(res_beefheart["plaatsen"]), 1)

        dp.set_alist([{"erkenningsNummer": "2"}])

        # after the alist should be reversed
        # zapp has lower sollnr
        # but beefheart is now on A-list
        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        res_zappa = alloc_erk("1", allocation)
        res_beefheart = alloc_erk("2", allocation)

        self.assertEqual(len(res_zappa["plaatsen"]), 1)
        self.assertEqual(len(res_beefheart["plaatsen"]), 3)

    def test_vpl_pref_to_soll_on_alist(self):
        """
        krijgt GEEN voorrang over VPLs
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # put 2 on the alist and retry
        self.dp.set_alist([{"erkenningsNummer": "2"}])

        # vpl should still get the stand
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        res = alloc_erk("1", allocation)
        self.assertListEqual(res["plaatsen"], ["1"])
