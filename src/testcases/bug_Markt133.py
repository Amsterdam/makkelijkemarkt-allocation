import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.utils import AllocationDebugger
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class TestMarkt133(unittest.TestCase):
    def test_not_correct_prefs_so_rejected(self):
        # meant as quick start blueprint to investigate allocation problems

        dp = FixtureDataprovider("../fixtures/bug_Markt133_rejected.json")
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        afwijzingen = market_allocation["afwijzingen"]

        afw_soll = [
            x
            for x in afwijzingen
            if x["ondernemer"]["erkenningsNummer"] == "2015061001"
        ]
        # Assert that sollicitant is in toewijzingen
        assert len(afw_soll) == 1
        assert len(market_allocation["toewijzingen"]) == 0

    def test_correct_prefs_so_accepted(self):
        # meant as quick start blueprint to investigate allocation problems

        dp = FixtureDataprovider("../fixtures/bug_Markt133_accepted.json")
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        toewijzingen = market_allocation["toewijzingen"]

        toew_soll = [
            x
            for x in toewijzingen
            if x["ondernemer"]["erkenningsNummer"] == "2015061001"
        ]
        # Assert that sollicitant is in toewijzingen
        assert len(toew_soll) == 1
        assert len(toew_soll[0]["plaatsen"]) == 3

    def test_with_neighbour(self):
        # meant as quick start blueprint to investigate allocation problems

        dp = FixtureDataprovider("../fixtures/bug_Markt133_neighbour.json")
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        toewijzingen = market_allocation["toewijzingen"]

        toew_soll = [
            x
            for x in toewijzingen
            if x["ondernemer"]["erkenningsNummer"] == "2015061001"
        ]
        # Assert that sollicitant is in toewijzingen
        assert len(toew_soll) == 1
        assert len(toew_soll[0]["plaatsen"]) == 3
