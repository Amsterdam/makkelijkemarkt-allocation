import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.utils import AllocationDebugger
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class Bug50364TestCase(unittest.TestCase):
    def test_soll_gets_two_stands(self):
        dp = FixtureDataprovider(
            "../fixtures/bug_50364_soll_does_not_get_2_stands.json"
        )
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        toewijzingen = market_allocation["toewijzingen"]
        soll = [
            x
            for x in toewijzingen
            if x["ondernemer"]["erkenningsNummer"] == "6070508211"
        ][0]
        db = AllocationDebugger(allocator.get_debug_data())

        # expect sollicitant to get single stand 51 instead of two in phase 23
        # then sollicitant will receive two new stands in phase 25 and relase stand 51
        previous_allocated_single_stand = "51"
        assert (
            db.get_allocation_phase_for_stand(previous_allocated_single_stand)
            == "stand: 51 -> Phase 23"
        )
        assert all(
            [previous_allocated_single_stand not in x["plaatsen"] for x in toewijzingen]
        )

        expected_stands = {"268", "270"}
        assert set(soll["plaatsen"]) & expected_stands == expected_stands
        for stand in expected_stands:
            assert "Phase 25" in db.get_allocation_phase_for_stand(stand)
