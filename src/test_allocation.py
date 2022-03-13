import unittest
from pprint import pprint
import json
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.outputdata import MarketArrangement
from kjk.outputdata import StandsTypeError
from kjk.rejection_reasons import (
    MINIMUM_UNAVAILABLE,
    MARKET_FULL,
    BRANCHE_FULL,
    ADJACENT_UNAVAILABLE,
    VPL_POSITION_NOT_AVAILABLE,
)
from kjk.utils import MarketStandClusterFinder
from kjk.utils import BranchesScrutenizer
from kjk.utils import AllocationDebugger
from kjk.utils import PreferredStandFinder
from kjk.utils import RejectionReasonManager
from kjk.test_utils import (
    print_alloc,
    stands_erk,
    alloc_erk,
    reject_erk,
    ErkenningsnummerNotFoudError,
)
from kjk.utils import TradePlacesSolver


class RejectionManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.sut = RejectionReasonManager()

    def test_add_rejection(self):
        self.sut.add_rejection_reason_for_merchant("1234", VPL_POSITION_NOT_AVAILABLE)
        reason = self.sut.get_rejection_reason_for_merchant("1234")
        self.assertEqual(reason["code"], 5)

    def test_add_deafault_rejection(self):
        reason = self.sut.get_rejection_reason_for_merchant("1234")
        self.assertEqual(reason["code"], 4)


class PreferredStandFinderTestCase(unittest.TestCase):
    def test_no_pref(self):
        pref = []
        cluster = ["1", "2", "3"]
        sut = PreferredStandFinder(cluster, pref)
        stds = sut.produce()
        self.assertListEqual(stds, ["1"])

    def test_pref(self):
        pref = ["2"]
        cluster = ["1", "2", "3"]
        sut = PreferredStandFinder(cluster, pref)
        stds = sut.produce()
        self.assertListEqual(stds, ["2"])

    def test_pref_2(self):
        pref = ["3", "5", "7", "2"]
        cluster = ["1", "2", "3"]
        sut = PreferredStandFinder(cluster, pref)
        stds = sut.produce()
        self.assertListEqual(stds, ["2"])


class AllocationDebuggerTestCase(unittest.TestCase):
    def setUp(self):
        data = {
            "Phase 10": [
                {"erk": "0162016063", "stands": ["64", "66"]},
                {"erk": "6012021081", "stands": ["8"]},
            ],
            "Phase 11": [
                {"erk": "4021992092", "stands": ["126"]},
                {"erk": "6041993100", "stands": ["98"]},
                {"erk": "3021997061", "stands": ["115"]},
                {"erk": "9022021060", "stands": ["224"]},
                {"erk": "1052016011", "stands": ["26"]},
            ],
            "Phase x": None,
        }
        self.sut = AllocationDebugger(data)

    def test_by_stand(self):
        result = self.sut.get_allocation_phase_for_stand("98")
        self.assertEqual("stand: 98 -> Phase 11", result)

    def test_by_merchant(self):
        result = self.sut.get_allocation_phase_for_merchant("6041993100")
        self.assertEqual("merchant: 6041993100 -> Phase 11", result)

    def test_by_unknwon_merchant(self):
        result = self.sut.get_allocation_phase_for_merchant("xx6041993100")
        self.assertEqual(None, result)

    def test_by_unknwon_merchant(self):
        result = self.sut.get_allocation_phase_for_stand("1234")
        self.assertEqual(None, result)


class TradePlacesSolverTestCase(unittest.TestCase):
    def setUp(self):
        self.data = {
            "123": {"fixed": ["1", "2"], "wanted": ["3", "4"]},
            "999": {"fixed": ["10", "11"], "wanted": ["7", "8"]},
            "666": {"fixed": ["8", "7"], "wanted": ["11", "10"]},
            "456": {"fixed": ["3"], "wanted": ["5"]},
            "789": {"fixed": ["5"], "wanted": ["3"]},
        }
        self.sut = TradePlacesSolver(self.data)

    def test_get_traders(self):
        res = self.sut.get_position_traders()
        self.assertListEqual(res, ["666", "999", "789", "456"])


class TestUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            "toewijzingen": [
                {"erkenningsNummer": "1", "plaatsen": ["1", "2"]},
                {"erkenningsNummer": "2", "plaatsen": ["4", "5"]},
            ],
            "afwijzingen": [{"erkenningsNummer": "3"}, {"erkenningsNummer": "4"}],
        }

    def test_alloc_erk(self):
        res = alloc_erk("1", self.test_data)
        self.assertEqual(res["erkenningsNummer"], "1")
        self.assertListEqual(res["plaatsen"], ["1", "2"])

    def test_stands_erk(self):
        res = stands_erk("1", self.test_data)
        self.assertListEqual(res, ["1", "2"])

    def test_reject_erk(self):
        res = reject_erk("3", self.test_data)
        self.assertEqual(res["erkenningsNummer"], "3")

    def test_exception_raised(self):
        with self.assertRaises(ErkenningsnummerNotFoudError):
            res = alloc_erk("123", self.test_data)
        with self.assertRaises(ErkenningsnummerNotFoudError):
            res = reject_erk("123", self.test_data)
        with self.assertRaises(ErkenningsnummerNotFoudError):
            res = stands_erk("123", self.test_data)


class BrancheScrutenizerTestCase(unittest.TestCase):
    """
    test data in fixture:
    {'101-agf': 15,
     '103-brood-banket': 4,
     '104-hummus-kruiden-olijven': 2,
     '105-noten-zuidvruchten': 4,
     '109-zuivel-eieren': 8,
     '110-poelier': 5,
     '111-exotische-groenten': 2,
     '206-oudhollands-gebak': 1,
     '207-grill-frituur': 4,
     '209-vis-gebakken': 8,
     '211-delicatessen-hapjes': 1,
     '302-bloemen-planten': 8,
     '401 - Overig markt - Experimentele zone': 12,
     'bak': 37}
    """

    def setUp(self):
        dp = FixtureDataprovider("../fixtures/test_input.json")
        dp.load_data()
        self.sut = BranchesScrutenizer(dp.get_branches())

    def test_max_branches(self):
        self.sut.add_allocation(["101-agf"])
        allowed = self.sut.allocation_allowed(["101-agf"])
        self.assertTrue(allowed)

        self.sut.add_allocation(["104-hummus-kruiden-olijven"])
        self.sut.add_allocation(["104-hummus-kruiden-olijven"])

        allowed = self.sut.allocation_allowed(["104-hummus-kruiden-olijven"])
        self.assertFalse(allowed)

    def test_max_bak(self):
        for alloc in range(35):
            self.sut.add_allocation(["404-broodje-bapao", "bak"])

        allowed = self.sut.allocation_allowed(["404-broodje-bapao", "bak"])
        self.assertTrue(allowed)

        for alloc in range(2):
            self.sut.add_allocation(["404-broodje-knakworst", "bak"])

        allowed = self.sut.allocation_allowed(["404-broodje-knakworst", "bak"])
        self.assertFalse(allowed)


class MockDataproviderTestCase(unittest.TestCase):
    def setUp(self):
        self.sut = MockDataprovider("../fixtures/test_input.json")

    def test_mock_market(self):
        self.sut.add_merchant(
            erkenningsNummer="1123456",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="123",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-afg"],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        res = self.sut.get_merchants()
        self.assertListEqual(
            res,
            [
                {
                    "erkenningsNummer": "1123456",
                    "plaatsen": ["1", "2"],
                    "status": "vpl",
                    "sollicitatieNummer": "123",
                    "description": "Frank Zappa",
                    "voorkeur": {
                        "branches": ["101-afg"],
                        "maximum": 2,
                        "minimum": 2,
                        "verkoopinrichting": [],
                        "absentFrom": "",
                        "absentUntil": "",
                    },
                }
            ],
        )

        self.sut.add_stand(
            plaatsId="1",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )
        self.sut.add_stand(
            plaatsId="2",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )
        self.assertEqual(len(self.sut.get_market_locations()), 2)

        self.sut.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)
        self.assertEqual(len(self.sut.get_branches()), 1)
        self.sut.add_rsvp(erkenningsNummer="1123456", attending=True)

        self.sut.mock()
        allocator = Allocator(self.sut)
        market_allocation = allocation = allocator.get_allocation()
        self.assertListEqual(
            alloc_erk("1123456", market_allocation)["plaatsen"], ["1", "2"]
        )


class ClusterFinderTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/test_input.json")
        dp.load_data()
        self.sut = MarketStandClusterFinder(
            dp.get_market_blocks(),
            dp.get_obstacles(),
            {"1": ["101-agf"]},
            {},
            {},
            [],
        )

    def test_find_cluster(self):
        res = self.sut.find_valid_cluster(
            ["2", "4", "123", "22", "7", "9", "11"], size=3
        )
        self.assertListEqual(["119", "121", "123"], res)
        res = self.sut.find_valid_cluster(["2", "4", "5", "7", "9", "11"], size=3)
        self.assertListEqual(["5", "7", "9"], res)
        res = self.sut.find_valid_cluster(
            ["197", "153", "151", "157", "155", "199", "201", "200", "198"], size=2
        )
        self.assertListEqual(["195", "197"], res)
        res = self.sut.find_valid_cluster(
            ["153", "151", "157", "155", "199", "201", "200", "198"],
            size=2,
        )
        self.assertListEqual(["151", "153"], res)

    def test_find_valid_expansion(self):
        res = self.sut.find_valid_expansion(["5", "7"], total_size=3)
        self.assertListEqual([["5", "7", "9"]], res)
        res = self.sut.find_valid_expansion(["213", "215"], total_size=3)
        self.assertListEqual([["211", "213", "215"], ["213", "215", "217"]], res)
        res = self.sut.find_valid_expansion(["246", "248"], total_size=3)
        self.assertListEqual([["244", "246", "248"]], res)
        res = self.sut.find_valid_expansion(["211", "213"], total_size=4)
        self.assertListEqual(
            [["207 - 209", "211", "213", "215"], ["211", "213", "215", "217"]], res
        )
        res = self.sut.find_valid_expansion(
            ["213", "215"], total_size=3, prefs=["999", "215"], preferred=True
        )
        self.assertListEqual(["211", "213", "215"], res)

    def test_get_neighbours(self):
        res = self.sut.get_neighbours_for_stand_id("155")
        self.assertDictEqual(res, {"prev": "153", "next": "157"})
        res = self.sut.get_neighbours_for_stand_id("15599")
        self.assertTrue(res is None)

    def test_max_not_available(self):
        res = self.sut.find_valid_cluster(["229"], size=12)
        self.assertListEqual([], res)
        res = self.sut.find_valid_cluster(["207 - 209"], size=1)
        self.assertListEqual(["207 - 209"], res)


class OutputLayoutTest(unittest.TestCase):
    def setUp(self):
        f = open("../fixtures/merchant_3000187072.json", "r")
        self.mock_merchant_obj = json.load(f)
        f.close()
        self.sut = MarketArrangement(market_id="16", market_date="2021-10-30")

    def test_add_allocation(self):
        self.sut.add_allocation("3000187072", [101, 102, 103], self.mock_merchant_obj)
        output = self.sut.to_data()
        self.assertEqual(len(output["toewijzingen"]), 1)
        self.assertListEqual(
            alloc_erk("3000187072", output)["plaatsen"], [101, 102, 103]
        )

    def test_raise_exception(self):
        try:
            self.sut.add_allocation("3000187072", 101, self.mock_merchant_obj)
            output = self.sut.to_data()
        except StandsTypeError:
            self.assertTrue(True)

    def test_add_multiple_allocation(self):
        self.sut.add_allocation("3000187072", [101, 102, 103], self.mock_merchant_obj)
        self.sut.add_allocation("3000187072", [4, 5], self.mock_merchant_obj)
        output = self.sut.to_data()
        self.assertEqual(len(output["toewijzingen"]), 1)
        self.assertListEqual(
            alloc_erk("3000187072", output)["plaatsen"], [4, 5, 101, 102, 103]
        )

    def test_add_rejection(self):
        self.sut.add_rejection(
            "3000187072", MINIMUM_UNAVAILABLE, self.mock_merchant_obj
        )
        output = self.sut.to_data()
        code = output["afwijzingen"][0]["reason"]["code"]
        self.assertEqual(1, len(output["afwijzingen"]))
        self.assertEqual(3, code)


class AllocatorTest(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/test_input.json")
        self.sut = Allocator(dp)

    def test_get_baking_positions(self):
        bak_pos = self.sut.get_baking_positions()
        expected_pos = [
            "2",
            "4",
            "23",
            "53",
            "81",
            "82",
            "83",
            "84",
            "85",
            "87",
            "89",
            "91",
            "100",
            "102",
            "119",
            "129",
            "130",
            "132",
            "171",
            "182",
            "184",
            "186",
            "187",
            "188",
            "189",
            "191",
            "219",
            "221",
            "207 - 209",
            "237",
            "239",
            "241",
        ]
        self.assertListEqual(bak_pos, expected_pos)

    def test_get_vpl_for_position(self):
        merchant = self.sut.get_vpl_for_position("81")
        self.assertEqual(merchant, "1020185000")

    def test_get_merchant_for_branche_vpl(self):
        merchants = self.sut.get_merchant_for_branche("101-agf", status="vpl")
        expected_merchants = [
            "0000182030",
            "2000180000",
            "0020181040",
            "6042004040",
            "5002008060",
        ]
        self.assertListEqual(merchants, expected_merchants)

    def test_get_merchant_for_branche(self):
        merchants = self.sut.get_merchant_for_branche("bak")
        expected_merchants = [
            "1020185000",
            "0000181012",
            "2000113080",
            "7000117002",
            "8032002080",
            "7002002000",
            "2002004040",
            "4022004040",
            "1062008080",
            "5022001050",
            "0042004002",
        ]
        self.assertListEqual(merchants, expected_merchants)
        merchants = self.sut.get_merchant_for_branche("bak", status="soll")
        expected_merchants = ["0042004002"]
        self.assertListEqual(merchants, expected_merchants)
        merchants = self.sut.get_merchant_for_branche("bak", status="vpl")
        expected_merchants = [
            "1020185000",
            "0000181012",
            "2000113080",
            "7000117002",
            "8032002080",
            "7002002000",
            "2002004040",
            "4022004040",
            "1062008080",
            "5022001050",
        ]
        self.assertListEqual(merchants, expected_merchants)

    def test_get_merchant_for_branche_soll_empty(self):
        merchants = self.sut.get_merchant_for_branche("101-agf", status="soll")
        expected_merchants = []
        self.assertListEqual(merchants, expected_merchants)

    def test_get_rsvp_for_merchat(self):
        rsvp = self.sut.get_rsvp_for_merchant("5002001062")
        self.assertFalse(rsvp)

    def test_add_prefs_for_merchant(self):
        # column prefs should be added in the constructor of sut
        columns = list(self.sut.merchants_df)
        self.assertIn("pref", columns)

    def test_get_merchants_with_evi(self):
        evis = self.sut.get_merchants_with_evi()
        expected_evis = [
            "6040188042",
            "2000178040",
            "1020185000",
            "0020181040",
            "2000113080",
            "7000117002",
            "2002004040",
            "4022004040",
            "5022001050",
            "1002002000",
            "7022008040",
            "0042004002",
            "0002020002",
        ]
        self.assertListEqual(evis, expected_evis)

    def test_get_pref_for_merchant(self):
        m = self.sut.get_prefs_for_merchant("1022020060")
        self.assertListEqual(
            m,
            [
                "195",
                "193",
                "230",
                "228",
                "225",
                "226",
                "204",
                "211",
                "223",
                "221",
                "222",
            ],
        )

    def test_dequeue_merchant(self):
        l1 = self.sut.num_merchants_in_queue()
        self.sut.dequeue_marchant("3000187072")
        l2 = self.sut.num_merchants_in_queue()
        self.assertEqual(l1, l2 + 1)

    def test_dequeque_stand(self):
        l1 = self.sut.num_stands_in_queue()
        self.sut.dequeue_market_stand("1")
        l2 = self.sut.num_stands_in_queue()
        self.assertEqual(l1, l2 + 1)

    def test_get_branhes_fro_stand(self):
        res = self.sut.get_branches_for_stand(1)
        self.assertListEqual(res, ["401 - Overig markt - Experimentele zone"])
        res = self.sut.get_branches_for_stand(999)
        self.assertListEqual(res, [])
        res = self.sut.get_branches_for_stand(245)
        self.assertListEqual(res, [])

    def test_add_alist_status_for_merchant(self):
        res = self.sut.add_alist_status_for_merchant()
        alist = self.sut.merchants_df["alist"]
        self.assertEqual(116, len(alist))
        self.assertTrue(alist[0])
        self.assertFalse(alist[3])

    def test_get_stand_for_branche(self):
        res = self.sut.get_stand_for_branche("101-agf")
        br = res.iloc[0]["branches"]
        self.assertIn("101-agf", br)


if __name__ == "__main__":
    from kjk.logging import *

    logging.disable(logging.CRITICAL)
    unittest.main()
    logging.disable(logging.NOTSET)
