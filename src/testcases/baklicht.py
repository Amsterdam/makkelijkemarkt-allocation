import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc, alloc_sollnr


class BaklichtTestCase(unittest.TestCase):
    def setUp(self):
        dp = FixtureDataprovider("../fixtures/bak-licht-ac-testdata.json")
        allocator = Allocator(dp)
        self.market_allocation = allocator.get_allocation()

    def test_bak_licht(self):
        # there is one bak-licht stand (nr 25)
        # and one bak-licht soll (9892) check if he gets the stand
        alloc = alloc_sollnr(9892, self.market_allocation)
        self.assertListEqual(alloc["plaatsen"], ["25"])


class BaklichtVsBakzwaarTestCase(unittest.TestCase):
    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchant 1 bak, soll
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=2,
            description="Frank Zappa",
            voorkeur={
                "branches": ["vis"],
                "maximum": 1,
                "minimum": 1,
                "bakType": "bak",
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # merchant 2 bak-licht, soll
        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=1,
            description="C Beefheart",
            voorkeur={
                "branches": ["worstjes"],
                "maximum": 1,
                "minimum": 1,
                "bakType": "bak-licht",
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # 2 stands one bak one bak-licht
        dp.add_page(["1", "2"])
        dp.add_stand(
            plaatsId="1",
            branches=[],
            bakType="bak",
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            bakType="bak",
            properties=[],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=1)
        dp.add_branche(brancheId="bak-licht", verplicht=True, maximumPlaatsen=2)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_assign_bak_stands(self):
        self.assertEqual(0, len(self.market_allocation["afwijzingen"]))

    def test_bak_zwaar_can_not_take_bak_licht_stand(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchant 1 bak, soll
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=2,
            description="Frank Zappa",
            voorkeur={
                "branches": ["vis"],
                "maximum": 1,
                "minimum": 1,
                "bakType": "bak",
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # merchant 2 bak-licht, soll
        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=1,
            description="C Beefheart",
            voorkeur={
                "branches": ["worstjes"],
                "maximum": 2,
                "minimum": 1,
                "bakType": "bak-licht",
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # 2 stands one bak one bak-licht
        dp.add_page(["1", "2"])
        dp.add_stand(
            plaatsId="1",
            branches=[],
            bakType="bak-licht",
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            bakType="bak-licht",
            properties=[],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=1)
        dp.add_branche(brancheId="bak-licht", verplicht=True, maximumPlaatsen=2)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        market_allocation = allocator.get_allocation()

        reject = reject_erk("1", market_allocation)
        alloc = alloc_erk("2", market_allocation)
        self.assertEqual(3, reject["reason"]["code"])
        self.assertEqual(2, len(alloc["plaatsen"]))
