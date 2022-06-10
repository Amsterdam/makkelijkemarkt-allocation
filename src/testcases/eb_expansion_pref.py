import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import print_alloc
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestEBExpansionPref(unittest.TestCase):
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
        alloc = alloc_erk("1", allocation)
        self.assertEqual(2, len(alloc["plaatsen"]))
        self.assertIn("2", alloc["plaatsen"])
        self.assertNotIn("1", alloc["plaatsen"])
        self.assertIn("3", alloc["plaatsen"])
