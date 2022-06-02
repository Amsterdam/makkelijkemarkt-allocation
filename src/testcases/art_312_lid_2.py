import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class Art_312_lid_2_TestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/art_312_lid_2.json")
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_pref_non_move(self):
        """
        merchant 10473 (Le Luc) should get expansion stand 146 because he did not move.
        even though merchant 9880 (van Goerle) has a better ranking/soll_nr
        This is stated in art 3.12.2 of the regulations
        """
        stds_1 = alloc_sollnr(9880, self.market_allocation)
        self.assertEqual(1, len(stds_1["plaatsen"]))

        stds_2 = alloc_sollnr(10473, self.market_allocation)
        self.assertEqual(2, len(stds_2["plaatsen"]))
        self.assertIn("146", stds_2["plaatsen"])
