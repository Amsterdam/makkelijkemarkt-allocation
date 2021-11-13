import unittest
from pprint import pprint
import json
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider
from kjk.outputdata import MarketArrangement
from kjk.outputdata import StandsTypeError
from kjk.outputdata import MINIMUM_UNAVAILABLE, MARKET_FULL, BRANCHE_FULL, ADJACENT_UNAVAILABLE


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
        dp = FixtureDataprovider("../fixtures/dapp_20211030/a_input.json")
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


if __name__ == '__main__':
    unittest.main()

