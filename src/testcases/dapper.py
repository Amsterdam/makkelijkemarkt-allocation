import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class DapperTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/dapp_20211030/a_input.json")
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_market_optimize(self):
        num_afw = len(self.market_allocation["afwijzingen"])
        print_alloc(self.market_allocation)
        self.assertEqual(num_afw, 2)

    def test_evi_alloc(self):
        res = alloc_erk("9012002010", self.market_allocation)
        for p in res["plaatsen"]:
            for mp in self.market_allocation["marktplaatsen"]:
                if mp["plaatsId"] == p:
                    self.assertIn("eigen-materieel", mp["verkoopinrichting"])


class DapperTestCase2(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/dapp_20211030/a_input-scen1.json")
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_market_optimize(self):
        num_afw = len(self.market_allocation["afwijzingen"])
        self.assertEqual(num_afw, 2)

    def test_6304_num_stands(self):
        tw = alloc_sollnr(6304, self.market_allocation)
        self.assertEqual(len(tw["plaatsen"]), 3)
