import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class DapperTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/dapp_20211030/a_input.json")
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_evi_alloc(self):
        res = alloc_erk("9012002010", self.market_allocation)
        self.assertListEqual(res["plaatsen"], ["195"])
