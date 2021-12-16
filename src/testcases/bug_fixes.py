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

# These tests all expose data quality bugs
# The bugs occurred while testing allocations on ACC data
# NOTE: There are no assertions, tests succeed if no exeptions are raised


class EviCrashBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/evi-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class BranchesCrashBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/branches-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class BranchesCrashBug2TestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/branches-bug2.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class AllocationBugA12TestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/12A-allocation-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class MaximumPlacesBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/maximum-plaatsen-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class MaximumPlacesBug2TestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/maximum-plaatsen-bug2.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class Phase00BugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/phase_00-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class ValueErrorBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/value-error-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()


class VplBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/vpl-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()