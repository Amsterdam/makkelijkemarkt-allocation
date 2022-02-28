import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import (
    alloc_erk,
    stands_erk,
    reject_erk,
    print_alloc,
    ErkenningsnummerNotFoudError,
)


class TestBasicAllocation(unittest.TestCase):
    """
    Een ondernemer die ingedeeld wil worden
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer=2,
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 2,
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
            sollicitatieNummer=2,
            description="C Beefheart",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 1,
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
            sollicitatieNummer=3,
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

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
            inactive=True,
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_assign_empty_stand(self):
        """
        wordt toegewezen aan een lege plek
        """
        stands = self.market_allocation["toewijzingen"]
        self.assertEqual(len(stands), 1)

    def test_assign_non_active_stands(self):
        """
        komt niet op een inactieve marktplaats
        """
        stands = self.market_allocation["toewijzingen"]
        for st in stands:
            pl = st["plaatsen"]
            self.assertNotIn(3, pl)

    def test_assign_standwerker(self):
        """
        komt op een standwerkerplaats als hij standwerker is
        """
        # exp merchants apperently have stands
        # so they will always be allocated to their stands
        self.dp.add_merchant(
            erkenningsNummer="4",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="4",
            description="Janus Standwerker",
            voorkeur={
                "branches": ["401-experimentele-zone"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_page(["1", "2", "3", "4", "5", "6", "7", "8", "9"])
        self.dp.add_rsvp(erkenningsNummer="4", attending=True)
        self.dp.add_stand(
            plaatsId="9",
            branches=["401-experimentele-zone"],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="3",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="4",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="5",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_branche(
            brancheId="401-experimentele-zone", verplicht=True, maximumPlaatsen=12
        )
        self.dp.mock()

        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        merchant_found = False
        for tw in market_allocation["toewijzingen"]:
            if tw["plaatsen"][0] == "9":
                merchant_found = True
                self.assertEqual("Janus Standwerker", tw["ondernemer"]["description"])
        self.assertTrue(merchant_found)

    def test_assign_unused_baking_stand(self):
        """
        komt op een bakplaats als deze niet gebruikt wordt
        """
        self.dp.add_merchant(
            erkenningsNummer="244",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=1,
            description="K. Oopman",
            voorkeur={
                "branches": ["vacuumslangen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_page(["7"])
        self.dp.add_rsvp(erkenningsNummer="244", attending=True)
        self.dp.add_stand(
            plaatsId="7",
            branches=["bak"],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=12)
        self.dp.mock()

        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        merchant_found = False
        for tw in market_allocation["toewijzingen"]:
            if tw["plaatsen"][0] == "7":
                merchant_found = True
                self.assertEqual("K. Oopman", tw["ondernemer"]["description"])
        self.assertTrue(merchant_found)

    def test_assign_unused_evi_stand(self):
        """
        komt op een EVI plaats als deze niet gebruikt wordt
        """
        self.dp.add_merchant(
            erkenningsNummer="244",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="1",
            description="K. Oopman",
            voorkeur={
                "branches": ["vacuumslangen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_page(["7"])
        self.dp.add_rsvp(erkenningsNummer="244", attending=True)
        self.dp.add_stand(
            plaatsId="7",
            branches=["bak"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
            inactive=False,
        )
        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=12)
        self.dp.mock()

        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        merchant_found = False
        for tw in market_allocation["toewijzingen"]:
            if tw["plaatsen"][0] == "7":
                merchant_found = True
                self.assertEqual("K. Oopman", tw["ondernemer"]["description"])
        self.assertTrue(merchant_found)

    def test_assign_rejected_stand(self):
        """
        komt op de plek van een afgewezen ondernemer, na een afwijzing wegens te weinig ruimte
        """
        self.dp.add_merchant(
            erkenningsNummer="23",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="999",
            description="G. Rootheidswaanzin",
            voorkeur={
                "branches": ["vacuumslangen"],
                "maximum": 23,
                "minimum": 22,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_merchant(
            erkenningsNummer="24",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="6",
            description="B.E. Scheiden",
            voorkeur={
                "branches": ["vacuumslangen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_branche(
            brancheId="vacuumslangen", verplicht=True, maximumPlaatsen=1
        )

        self.dp.add_page(["1", "2", "3", "4", "5", "6", "7", "8", "9"])
        self.dp.add_rsvp(erkenningsNummer="24", attending=True)
        self.dp.add_rsvp(erkenningsNummer="23", attending=True)
        self.dp.add_stand(
            plaatsId="3",
            branches=["bak"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="4",
            branches=["bak"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="5",
            branches=["vacuumslangen"],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="6",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="7",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="8",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_stand(
            plaatsId="9",
            branches=[],
            properties=[],
            verkoopinrichting=[],
            inactive=False,
        )
        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=12)
        self.dp.mock()

        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        res = alloc_erk("24", market_allocation)
        self.assertListEqual(res["plaatsen"], ["5"])
        res = reject_erk("23", market_allocation)
        with self.assertRaises(ErkenningsnummerNotFoudError):
            reject_erk("24", market_allocation)
