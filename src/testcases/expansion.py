import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider


class TestExpansion(unittest.TestCase):
    """
    Een ondernemer die wil uitbreiden
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 4,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="12",
            description="C Beefheart",
            voorkeur={
                "branches": ["101-bbb"],
                "maximum": 3,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="3",
            description="J Medeski",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # add pages
        dp.add_page([None, "1", "2", "3", "4", None])
        dp.add_page([None, "5", "6", "7", None])

        # prefs
        dp.add_pref(erkenningsNummer="3", plaatsId="7", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="5", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="6", priority=1)

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        dp.add_stand(
            plaatsId="4",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        dp.add_stand(
            plaatsId="5",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        dp.add_stand(
            plaatsId="6",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        dp.add_stand(
            plaatsId="7",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        # dp.mock()
        # allocator = Allocator(dp)
        # self.market_allocation = allocation = allocator.get_allocation()

    def test_stay_in_same_row(self):
        """
        blijft binnen dezelfde marktkraamrij
        """
        res = self.market_allocation["toewijzingen"][0]["plaatsen"]
        res.sort()
        self.assertListEqual(res, ["1", "2", "3", "4"])

    def test_can_have_second_stand(self):
        """
        kan een 2de plaats krijgen
        """
        res = self.market_allocation["toewijzingen"][0]["plaatsen"]
        self.assertTrue(len(res) > 2)

    def test_will_get_following_stands(self):
        """
        krijgt aaneensluitende plaatsen
        """
        res = self.market_allocation["toewijzingen"][0]["plaatsen"]
        res.sort()
        self.assertListEqual(res, ["1", "2", "3", "4"])

    def test_get_2_extra_if_space_sufficient(self):
        """
        krijgt gelijk twee plaatsen als er genoeg ruimte op de markt is
        """
        res = self.market_allocation["toewijzingen"][0]["plaatsen"]
        self.assertTrue(len(res) == 4)

    def test_more_tand_two_stands_must_wait(self):
        """
        naar meer dan 2 plaatsen moet wachten op iedereen die 2 plaatsen wil
        """
        pass

    def test_can_have_3_stands(self):
        """
        kan 3 plaatsen krijgen
        """
        res = self.market_allocation["toewijzingen"][0]["plaatsen"]
        self.assertTrue(len(res) > 2)

    def test_must_stay_in_branche_location(self):
        """
        kan niet uitbreiden naar een niet-branche plaats als zijn branche verplicht is
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="2",
            description="Dweezil Zappa",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 4,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        stds = allocation["toewijzingen"][0]["plaatsen"]
        self.assertListEqual(stds, ["1", "2"])

    def test_must_stay_in_evi_location(self):
        """
        kan niet uitbreiden naar een niet-EVI plaats indien zij een EVI hebben
        """
        pass

    def test_must_obey_expansion_limits(self):
        """
        kan niet verder vergroten dan is toegestaan
        """
        pass

    def test_can_not_get_obstacle_stand(self):
        """
        kan dat niet naar een zijde met een obstakel
        """
        pass

    def test_can_provide_min_stands(self):
        """
        kan een minimum aantal gewenste plaatsen opgeven
        """
        pass

    def test_can_provide_nax_stands(self):
        """
        kan een maximum aantal gewenste plaatsen opgeven
        """
        pass

    def test_gets_rejected_if_not_min(self):
        """
        wordt afgewezen als niet aan zijn minimum gewenste plaatsen wordt voldaan
        """
        pass

    def test_expansion_must_obey_max_branche_stands(self):
        """
        kan dat niet indien het maximum aantal branche-plaatsen wordt overschreden
        """
        pass

    def test_get_expansion_to_pref_side(self):
        """
        krijgt extra plaats(en) aan hun voorkeurszijde
        """
        pass

    def test_expansion_circular_market(self):
        """
        kan dit in een cirkelvormige marktoptstelling
        """
        pass
