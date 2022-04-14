import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class BaklichtTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/bak-licht-ac-testdata.json")
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_bak_licht(self):
        # there is one bak-licht stand (nr 25)
        # and one bak-licht soll (9892) check if he gets the stand
        alloc = alloc_sollnr(9892, self.market_allocation)
        self.assertListEqual(alloc["plaatsen"], ["25"])
