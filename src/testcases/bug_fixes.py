import unittest
from pprint import pprint
from kjk.utils import AllocationDebugger
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider
from kjk.test_utils import (
    print_alloc,
    stands_erk,
    alloc_erk,
    alloc_sollnr,
    reject_erk,
    reject_sollnr,
    ErkenningsnummerNotFoudError,
)

# These tests all expose data quality bugs
# The bugs occurred while testing allocations on ACC data
# NOTE: There are no assertions, tests succeed if no exeptions are raised


class BugFixBadAbsenceDates(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/absent_field_bug.json")
        self.allocator = Allocator(dp)
        self.market_allocation = self.allocator.get_allocation()

    def test_bug(self):
        num_afw = len(self.market_allocation["afwijzingen"])
        self.assertEqual(num_afw, 0)


class BugFixStand122TestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/bug_06-02-2022.json")
        self.allocator = Allocator(dp)
        self.market_allocation = self.allocator.get_allocation()

    def test_bug_stand_122(self):
        afw = reject_sollnr(220, self.market_allocation)
        stds = afw["ondernemer"]["plaatsen"]
        self.assertListEqual(stds, ["122"])
        self.assertEqual(afw["reason"]["code"], 5)


class DapperBugTestCase_3(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/bug_27-01-2022b.json")
        self.allocator = Allocator(dp)
        self.market_allocation = self.allocator.get_allocation()

    def test_rejections(self):
        num_rejects = len(self.market_allocation["afwijzingen"])
        self.assertEqual(5, num_rejects)

    def test_bug_1(self):
        # soll 110 should get 46
        tw = alloc_sollnr(110, self.market_allocation)
        self.assertListEqual(tw["plaatsen"], ["46"])

    def test_bug_2(self):
        # soll 70 should get 44
        tw = alloc_sollnr(70, self.market_allocation)
        self.assertListEqual(tw["plaatsen"], ["44"])

    def test_bug_4(self):
        # soll 73 should get 122
        # because vpl on 120 dropped this stand in prefs
        tw = alloc_sollnr(73, self.market_allocation)
        self.assertListEqual(tw["plaatsen"], ["77"])

    def test_rejection_minimum(self):
        afw = reject_sollnr(67, self.market_allocation)
        self.assertEqual(afw["reason"]["code"], 3)

    def test_reduction_number_of_stands_vpl(self):
        tw = alloc_sollnr(63, self.market_allocation)
        self.assertListEqual(tw["plaatsen"], ["75"])
        tw = alloc_sollnr(278, self.market_allocation)
        self.assertListEqual(tw["plaatsen"], ["120"])


class DapperMovingVplBugTestCase_2(unittest.TestCase):
    """Tuithof must be on 53 !"""

    def setUp(self):
        dp = FixtureDataprovider("../fixtures/bug_21-01-2022.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()

        erk = alloc_erk("8061993072", market_allocation)
        self.assertListEqual(erk["plaatsen"], ["53"])


class DapperMovingVplBugTestCase(unittest.TestCase):
    """should not crash on missing stand 122"""

    def setUp(self):
        dp = FixtureDataprovider("../fixtures/bug_20-01-2022.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()

        # db = AllocationDebugger(self.allocator.get_debug_data())
        # res = db.get_allocation_phase_for_merchant("1991061901")
        # print(res)
        res = reject_erk("1012003061", market_allocation)
        self.assertEqual(res["reason"]["code"], 5)


class NonRequiredBrancheBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/bug_13-01-2022.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()

        # print_alloc(market_allocation)
        db = AllocationDebugger(self.allocator.get_debug_data())
        res = db.get_allocation_phase_for_merchant("0012019022")  # Jansse
        # print(res)
        res = db.get_allocation_phase_for_merchant("7012011020")  # Schuurmans
        # print(res)

        erk = alloc_erk("7022013071", market_allocation)
        self.assertListEqual(erk["plaatsen"], ["14"])

        erk = alloc_erk("7012011020", market_allocation)
        erk["plaatsen"].sort()
        a = ["18", "17"]
        a.sort()
        self.assertListEqual(erk["plaatsen"], a)

        erk = alloc_erk("9012010012", market_allocation)
        erk["plaatsen"].sort()
        a = ["16", "15"]
        a.sort()
        self.assertListEqual(erk["plaatsen"], a)

        num_afw = len(market_allocation["afwijzingen"])
        num_tw = len(market_allocation["toewijzingen"])

        self.assertEqual(num_afw, 4)
        self.assertEqual(num_tw, 9)


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


class DapperBugTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/dapper-acc-bug.json")
        self.allocator = Allocator(dp)

    def test_bug(self):
        market_allocation = self.allocator.get_allocation()
