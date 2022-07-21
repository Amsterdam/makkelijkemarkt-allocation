import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.utils import AllocationDebugger
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class Bug50364TestCase(unittest.TestCase):
    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        dp.add_page(["1", "2", "3", "4"])
        dp.add_stand(plaatsId="1", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId="2", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId="3", branches=[], properties=[], verkoopinrichting=[])
        dp.add_stand(plaatsId="4", branches=[], properties=[], verkoopinrichting=[])

        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1"],
            status="eb",
            sollicitatieNummer="1",
            description="EB 1",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=["2"],
            status="eb",
            sollicitatieNummer="3",
            description="EB 2",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Sollicitant",
            voorkeur={
                "branches": [],
                "maximum": 2,
                "minimum": 1,
                "anywhere": True,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_pref(erkenningsNummer="2", plaatsId="1", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=2)
        dp.set_alist([{"erkenningsNummer": "2"}])
        self.dp = dp

    def _test_crash(self):
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        toewijzingen = allocation['toewijzingen']

        db = AllocationDebugger(allocator.get_debug_data())
        merchant_phase = db.get_allocation_phase_for_merchant('2')
        stand_3_phase = db.get_allocation_phase_for_stand('3')
        stand_4_phase = db.get_allocation_phase_for_stand('4')

        allocated = alloc_erk("2", allocation)
        pass

    def test_real(self):
        dp = FixtureDataprovider("../fixtures/bug_50364_soll_does_not_get_2_stands.json")
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()
        toewijzingen = market_allocation['toewijzingen']
        soll = [x for x in toewijzingen if x['ondernemer']['erkenningsNummer'] == '6070508211'][0]
        db = AllocationDebugger(allocator.get_debug_data())
        merchant_phase = db.get_allocation_phase_for_merchant('2016070508')
        stand_phase = db.get_allocation_phase_for_stand('51')
        # soll nr 12356
        expected_stands = {'268', '270'}
        assert set(soll['plaatsen']) & expected_stands == expected_stands
