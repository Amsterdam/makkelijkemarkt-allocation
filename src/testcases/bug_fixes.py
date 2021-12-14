import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider
from kjk.test_utils import (
    print_alloc,
    stands_erk,
    alloc_erk,
    reject_erk,
    ErkenningsnummerNotFoudError,
)


class EviCrashBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/evi-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class BaranchesCrashBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/branches-bug2.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()
