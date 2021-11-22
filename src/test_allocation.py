import unittest
from pprint import pprint
import json
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.outputdata import MarketArrangement
from kjk.outputdata import StandsTypeError
from kjk.outputdata import MINIMUM_UNAVAILABLE, MARKET_FULL, BRANCHE_FULL, ADJACENT_UNAVAILABLE
from kjk.utils import MarketStandClusterFinder


class MockDataproviderTestCase(unittest.TestCase):
    def setUp(self):
        self.sut = MockDataprovider("../fixtures/test_input.json")

    def test_mock_market(self):
        self.sut.add_merchant(erkenningsNummer='1123456',
                               plaatsen=['1', '2'],
                               status='vpl',
                               sollicitatieNummer="123",
                               description='Frank Zappa',
                               voorkeur={"branches": ['101-afg'], "maximum": 2, "minimum": 2, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})
        res = self.sut.get_merchants()
        self.assertListEqual(res, [{'erkenningsNummer': '1123456', 'plaatsen': ['1', '2'], 'status': 'vpl',
                                    'sollicitatieNummer': '123', 'description': 'Frank Zappa',
                                    'voorkeur': {'branches': ['101-afg'], 'maximum': 2, 'minimum': 2,
                                                 'verkoopinrichting': [], 'absentFrom': '', 'absentUntil': ''}}])

        self.sut.add_stand(plaatsId='1', branches=['101-agf'], properties=['boom'], verkoopinrichting=[])
        self.sut.add_stand(plaatsId='2', branches=['101-agf'], properties=['boom'], verkoopinrichting=[])
        self.assertEquals(len(self.sut.get_market_locations()), 2)

        self.sut.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)
        self.assertEquals(len(self.sut.get_branches()), 1)
        self.sut.add_rsvp(erkenningsNummer='1123456', attending=True)

        self.sut.mock()
        allocator = Allocator(self.sut)
        market_allocation = allocation = allocator.get_allocation()
        stands = market_allocation['toewijzingen'][0]['plaatsen']
        erk = market_allocation['toewijzingen'][0]['erkenningsNummer']
        self.assertEquals(erk, '1123456')
        self.assertListEqual(stands, ['1', '2'])


class ClusterFinderTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/test_input.json")
        dp.load_data()
        self.sut = MarketStandClusterFinder(dp.get_market_blocks(), dp.get_obstacles())

    def test_find_cluster(self):
        res = self.sut.find_valid_cluster(['2', '4', '123', '22', '7', '9', '11'], size=3)
        self.assertListEqual([], res)
        res = self.sut.find_valid_cluster(['2', '4', '123', '22', '5', '7', '9', '11'], size=3)
        self.assertListEqual([['5', '7', '9']], res)
        res = self.sut.find_valid_cluster(['197', '153', '151', '157', '155', '199', '201', '200', '198'], size=2)
        self.assertListEqual([['151', '153'], ['155', '157'], ['198', '200'], ['199', '201']], res)
        res = self.sut.find_valid_cluster(['197', '153', '151', '157', '155', '199', '201', '200', '198'], size=2, preferred=True)
        self.assertListEqual(['151', '153'], res)

    def test_find_valid_expansion(self):
        res = self.sut.find_valid_expansion(['5', '7'], total_size=3)
        self.assertListEqual([['5', '7', '9']], res)
        res = self.sut.find_valid_expansion(['213', '215'], total_size=3)
        self.assertListEqual([['211', '213', '215'], ['213', '215', '217']], res)
        res = self.sut.find_valid_expansion(['246', '248'], total_size=3)
        self.assertListEqual([['244', '246', '248']], res)
        res = self.sut.find_valid_expansion(['211', '213'], total_size=4)
        self.assertListEqual([['207 - 209', '211', '213', '215'], ['211', '213', '215', '217']], res)
        res = self.sut.find_valid_expansion(['213', '215'], total_size=3, prefs=['999', '215'], preferred=True)
        self.assertListEqual(['211', '213', '215'], res)

    def test_get_neighbours(self):
        res = self.sut.get_neighbours_for_stand_id('155')
        self.assertDictEqual(res, {'prev': '153', 'next': '157'})
        res = self.sut.get_neighbours_for_stand_id('15599')
        self.assertTrue(res is None)

    def test_max_not_available(self):
        res = self.sut.find_valid_cluster(['207 - 209'], size=2, preferred=True)
        self.assertListEqual([], res)
        res = self.sut.find_valid_cluster(['207 - 209'], size=1, preferred=True)
        self.assertListEqual(['207 - 209'], res)


class OutputLayoutTest(unittest.TestCase):
    def setUp(self):
        f = open('../fixtures/merchant_3000187072.json', 'r')
        self.mock_merchant_obj = json.load(f)
        f.close()
        self.sut = MarketArrangement(market_id="16", market_date="2021-10-30")

    def test_add_allocation(self):
        self.sut.add_allocation('3000187072', [101, 102, 103], self.mock_merchant_obj)
        output = self.sut.to_data()
        self.assertEqual(len(output['toewijzingen']), 1)
        self.assertListEqual(output['toewijzingen'][0]['plaatsen'], [101, 102, 103])

    def test_raise_exception(self):
        try:
            self.sut.add_allocation('3000187072', 101, self.mock_merchant_obj)
            output = self.sut.to_data()
        except StandsTypeError as e:
            self.assertTrue(True)

    def test_add_multiple_allocation(self):
        self.sut.add_allocation('3000187072', [101, 102, 103], self.mock_merchant_obj)
        self.sut.add_allocation('3000187072', [4, 5], self.mock_merchant_obj)
        output = self.sut.to_data()
        self.assertEqual(len(output['toewijzingen']), 1)
        self.assertListEqual(output['toewijzingen'][0]['plaatsen'], [101, 102, 103, 4, 5])

    def test_add_rejection(self):
        self.sut.add_rejection('3000187072', MINIMUM_UNAVAILABLE, self.mock_merchant_obj)
        output = self.sut.to_data()
        code = output['afwijzingen'][0]['reason']['code']
        self.assertEqual(1, len(output['afwijzingen']))
        self.assertEqual(3, code)


class AllocatorTest(unittest.TestCase):

    def setUp(self):
        dp = FixtureDataprovider("../fixtures/test_input.json")
        self.sut = Allocator(dp)

    def test_get_baking_positions(self):
        bak_pos = self.sut.get_baking_positions()
        expected_pos = ['2', '4', '23', '53', '81', '82', '83', '84', '85', '87', '89', '91', 
                        '100', '102', '119', '129', '130', '132', '171', '182', '184', '186', 
                        '187', '188', '189', '191', '219', '221', 
                        '207 - 209', '237', '239', '241']
        self.assertListEqual(bak_pos, expected_pos)

    def test_get_vpl_for_position(self):
        merchant = self.sut.get_vpl_for_position('81')
        self.assertEqual(merchant, '1020185000')

    def test_get_merchant_for_branche_vpl(self):
        merchants = self.sut.get_merchant_for_branche('101-agf', status="vpl")
        expected_merchants = ['0000182030', '2000180000', '0020181040', '6042004040', '5002008060']
        self.assertListEqual(merchants, expected_merchants)

    def test_get_merchant_for_branche(self):
        merchants = self.sut.get_merchant_for_branche('bak')
        expected_merchants = ['1020185000', '0000181012', '2000113080', '7000117002', 
                              '8032002080', '7002002000', '2002004040', '4022004040', 
                              '1062008080', '5022001050', '0042004002']
        self.assertListEqual(merchants, expected_merchants)
        merchants = self.sut.get_merchant_for_branche('bak', status="soll")
        expected_merchants = ['0042004002']
        self.assertListEqual(merchants, expected_merchants)
        merchants = self.sut.get_merchant_for_branche('bak', status="vpl")
        expected_merchants = ['1020185000', '0000181012', '2000113080', '7000117002', '8032002080', 
                              '7002002000', '2002004040', '4022004040', '1062008080', '5022001050']
        self.assertListEqual(merchants, expected_merchants)

    def test_get_merchant_for_branche_soll_empty(self):
        merchants = self.sut.get_merchant_for_branche('101-agf', status="soll")
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
        expected_evis = ['6040188042', '2000178040', '1020185000', '0020181040', '2000113080', 
                         '7000117002', '2002004040', '4022004040', '5022001050', '1002002000', 
                         '7022008040', '0042004002', '0002020002']
        self.assertListEqual(evis, expected_evis)

    def test_get_pref_for_merchant(self):
        m = self.sut.get_prefs_for_merchant('1022020060')
        self.assertListEqual(m, ['195', '193', '230', '228', '225', '226', '204', '211', '223', '221', '222'])

    def test_dequeue_merchant(self):
        l1 = self.sut.num_merchants_in_queue()
        self.sut.dequeue_marchant("3000187072")
        l2 = self.sut.num_merchants_in_queue()
        self.assertEqual(l1, l2+1)

    def test_dequeque_stand(self):
        l1 = self.sut.num_stands_in_queue()
        self.sut.dequeue_market_stand("1")
        l2 = self.sut.num_stands_in_queue()
        self.assertEqual(l1, l2+1)

    def test_get_branhes_fro_stand(self):
        res = self.sut.get_branches_for_stand(1)
        self.assertListEqual(res, ['401 - Overig markt - Experimentele zone'])
        res = self.sut.get_branches_for_stand(999)
        self.assertListEqual(res, [])
        res = self.sut.get_branches_for_stand(245)
        self.assertListEqual(res, [])

    def test_add_alist_status_for_merchant(self):
        res = self.sut.add_alist_status_for_merchant()
        alist = self.sut.merchants_df['alist']
        self.assertEqual(116, len(alist))
        self.assertTrue(alist[0])
        self.assertFalse(alist[3])

    def test_get_stand_for_branche(self):
        res = self.sut.get_stand_for_branche('101-agf')
        br = res.iloc[0]['branches']
        self.assertIn('101-agf', br)


if __name__ == '__main__':
    unittest.main()

