import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import print_alloc
from kjk.test_utils import alloc_erk, alloc_sollnr, stands_erk, reject_erk, print_alloc
from kjk.utils import AllocationDebugger


class TestEBExpansionPrefWithMock(unittest.TestCase):
    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["2"],
            status="eb",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["404-parfum"],
                "maximum": 2,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=1)

        # stands
        dp.add_page(["1", "2", "3"])
        dp.add_stand(plaatsId="1", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId="2", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId="3", branches=[], properties=[], verkoopinrichting=[])

        self.dp = dp

    def test_eb_expansion_direction(self):
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        allocated = alloc_erk("1", allocation)
        self.assertEqual(2, len(allocated["plaatsen"]))
        self.assertIn("2", allocated["plaatsen"])  # vaste plaats
        self.assertIn("3", allocated["plaatsen"])  # uitbreiding: get preferred 3
        self.assertNotIn("1", allocated["plaatsen"])

    # def test_eb_expansion_with_sollicitant_on_same_stand_and_anywhere_true(self):
    #     self.dp.add_merchant(
    #         erkenningsNummer="2",
    #         plaatsen=[],
    #         status="soll",
    #         sollicitatieNummer="222",
    #         description="Sollicitant",
    #         voorkeur={
    #             "branches": [],
    #             "maximum": 1,
    #             "minimum": 1,
    #             "anywhere": False,
    #         },
    #     )
    #     self.dp.add_pref(erkenningsNummer="2", plaatsId="3", priority=1)
    #     self.dp.add_rsvp(erkenningsNummer="2", attending=True)
    #     self.dp.set_alist([{"erkenningsNummer": "2"}])
    #     self.dp.update_merchant(
    #         erkenningsNummer="1",
    #         plaatsen=["2"],
    #         status="eb",
    #         sollicitatieNummer="2",
    #         description="Frank Zappa",
    #         voorkeur={
    #             "branches": ["404-parfum"],
    #             "maximum": 2,
    #             "minimum": 1,
    #             "verkoopinrichting": [],
    #             "absentFrom": "",
    #             "absentUntil": "",
    #             "anywhere": True,
    #         },
    #     )
    #     self.dp.mock()
    #     allocator = Allocator(self.dp)
    #     allocation = allocator.get_allocation()

    #     allocated_1 = alloc_erk("1", allocation)
    #     self.assertEqual(2, len(allocated_1["plaatsen"]))
    #     self.assertIn("2", allocated_1["plaatsen"])  # vaste plaats
    #     self.assertIn(
    #         "1", allocated_1["plaatsen"]
    #     )  # uitbreiding: 1 instead of preferred 3
    #     self.assertNotIn(
    #         "3", allocated_1["plaatsen"]
    #     )  # 3 should be obtained by Sollicitant

    #     allocated_2 = alloc_erk("2", allocation)
    #     self.assertEqual(1, len(allocated_2["plaatsen"]))
    #     self.assertIn("3", allocated_2["plaatsen"])  # Sollicitant got priority on 3

    # def test_eb_expansion_with_sollicitant_on_same_stand_and_anywhere_false(self):
    #     self.dp.add_merchant(
    #         erkenningsNummer="2",
    #         plaatsen=[],
    #         status="soll",
    #         sollicitatieNummer="222",
    #         description="Sollicitant",
    #         voorkeur={
    #             "branches": [],
    #             "maximum": 1,
    #             "minimum": 1,
    #             "anywhere": False,
    #         },
    #     )
    #     self.dp.add_pref(erkenningsNummer="2", plaatsId="3", priority=1)
    #     self.dp.add_rsvp(erkenningsNummer="2", attending=True)
    #     self.dp.set_alist([{"erkenningsNummer": "2"}])
    #     self.dp.update_merchant(
    #         erkenningsNummer="1",
    #         plaatsen=["2"],
    #         status="eb",
    #         sollicitatieNummer="2",
    #         description="Frank Zappa",
    #         voorkeur={
    #             "branches": ["404-parfum"],
    #             "maximum": 2,
    #             "minimum": 1,
    #             "verkoopinrichting": [],
    #             "absentFrom": "",
    #             "absentUntil": "",
    #             "anywhere": False,
    #         },
    #     )
    #     self.dp.mock()
    #     allocator = Allocator(self.dp)
    #     allocation = allocator.get_allocation()

    #     allocated_1 = alloc_erk("1", allocation)
    #     self.assertEqual(
    #         1, len(allocated_1["plaatsen"])
    #     )  # should get one place because expansion place is taken
    #     self.assertIn("2", allocated_1["plaatsen"])  # vaste plaats
    #     self.assertNotIn(
    #         "3", allocated_1["plaatsen"]
    #     )  # 3 should be obtained by Sollicitant

    #     allocated_2 = alloc_erk("2", allocation)
    #     self.assertEqual(1, len(allocated_2["plaatsen"]))
    #     self.assertIn("3", allocated_2["plaatsen"])  # Sollicitant got priority on 3


class TestEBExpansionPref(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/eb-expansion-prefs.json")
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_eb_expansion_direction(self):
        allocated = alloc_sollnr(9744, self.market_allocation)
        self.assertEqual(2, len(allocated["plaatsen"]))
        self.assertIn("189", allocated["plaatsen"])  # vaste plaats
        self.assertIn(
            "191", allocated["plaatsen"]
        )  # uitbreiding: 191 instead of preferred 189
        self.assertNotIn(
            "187", allocated["plaatsen"]
        )  # without pref 187 would be allocated
