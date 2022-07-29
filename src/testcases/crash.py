import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.utils import AllocationDebugger
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class CrashTestCase(unittest.TestCase):
    def test_with_fixture(self):
        # meant as quick start blueprint to investigate allocation problems
        #
        # dp = FixtureDataprovider("../fixtures/crash.json")
        # allocator = Allocator(dp)
        # market_allocation = allocator.get_allocation()
        # toewijzingen = market_allocation["toewijzingen"]
        #
        # soll = [
        #     x
        #     for x in toewijzingen
        #     if x["ondernemer"]["erkenningsNummer"] == "6070508211"
        # ][0]
        # db = AllocationDebugger(allocator.get_debug_data())
        # merchant_phase = db.get_allocation_phase_for_merchant('6070508211')
        # stand_phase = db.get_allocation_phase_for_stand('51')
        # expected_stands = {"268", "270"}
        # assert set(soll["plaatsen"]) & expected_stands == expected_stands
        assert True
