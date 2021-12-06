import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestRequiredBranches(unittest.TestCase):
    """
    Een ondernemer in een verplichte branche (bijv. bak)
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # branches
        dp.add_branche(
            brancheId="101-cosmic-utensils", verplicht=True, maximumPlaatsen=2
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)

        # add pages
        dp.add_page([None, "1", "2", "3", "4", None])
        dp.add_page([None, "5", "6", "7", None])

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
            branches=["101-cosmic-utensils"],
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

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_required_branche_stand(self):
        """
        kan enkel op een brancheplek staan
        """
        # should get 3
        twz = alloc_erk("1", self.market_allocation)
        self.assertListEqual(twz["plaatsen"], ["3"])

    def test_assign_most_suitable_stand(self):
        """
        komt op de meest geschikte brancheplaats te staan
        """
        # Branche overlap is belangrijker dan de prioritering van de ondernemer.
        self.dp.add_pref(erkenningsNummer="1", plaatsId="4", priority=1)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        twz = alloc_erk("1", allocation)
        # should get 3 although his prefs are 4 (4 is not branched)
        self.assertListEqual(twz["plaatsen"], ["3"])

    def test_can_not_expand_to_non_branche_stand(self):
        """
        kan niet uitbreiden naar een niet-branche plaats
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 2,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        # should only get 3 there is no room for branched exapnsion
        twz = alloc_erk("1", allocation)
        self.assertListEqual(twz["plaatsen"], ["3"])

    def test_reject_if_branche_stands_unavailable(self):
        """
        wordt afgewezen als er geen brancheplaatsen meer beschikbaar zijn
        """
        self.dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="0",
            description="Terry Bozio",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # rsvp
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        twz = alloc_erk("2", allocation)
        afw = reject_erk("1", allocation)
        self.assertEqual(twz["ondernemer"]["erkenningsNummer"], "2")
        self.assertEqual(afw["ondernemer"]["erkenningsNummer"], "1")

    def test_reject_if_max_branches_reached(self):
        """
        wordt afgewezen als het maximum aantal branche-ondernemers bereikt is
        """
        self.dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="3",
            description="Terry Bozio",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # rsvp
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        self.dp.add_merchant(
            erkenningsNummer="3",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="4",
            description="Sheik Yerbutti",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        # rsvp
        self.dp.add_rsvp(erkenningsNummer="3", attending=True)

        # add some more branched stands
        self.dp.add_page([None, "8", "9", "10", None])

        # stands
        self.dp.add_stand(
            plaatsId="8",
            branches=["101-cosmic-utensils"],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_stand(
            plaatsId="9",
            branches=["101-cosmic-utensils"],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_stand(
            plaatsId="10",
            branches=["101-cosmic-utensils"],
            properties=[],
            verkoopinrichting=[],
        )

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        # branche max is 2 merchants
        self.assertEqual(len(allocation["toewijzingen"]), 2)
        self.assertEqual(len(allocation["afwijzingen"]), 1)

    def test_pref_vpl_moving(self):
        """
        krijgt voorrang boven VPLs die willen verplaatsen
        """
        self.dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="3",
            description="Terry Bozio",
            voorkeur={
                "branches": ["404-lost-and-found"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # rsvp
        self.dp.add_rsvp(erkenningsNummer="2", attending=True)

        # pref
        self.dp.add_pref(erkenningsNummer="2", plaatsId="3", priority=1)

        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        twz_1 = alloc_erk("2", allocation)
        twz_2 = alloc_erk("1", allocation)
        self.assertEqual(twz_1["ondernemer"]["erkenningsNummer"], "2")
        self.assertEqual(twz_2["ondernemer"]["erkenningsNummer"], "1")
        self.assertListEqual(twz_1["plaatsen"], ["1"])
        self.assertListEqual(twz_2["plaatsen"], ["3"])

    def test_pref_to_soll_in_non_required_branches(self):
        """
        krijgt voorrang boven sollicitanten niet in een verplichte branche
        """
        # Altijd eerst brancheplaatsen proberen vullen met branche ondernemers.
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=["1"],
            status="soll",
            sollicitatieNummer="3",
            description="Terry Bozio",
            voorkeur={
                "branches": ["404-lost-and-found"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # branches
        dp.add_branche(
            brancheId="101-cosmic-utensils", verplicht=True, maximumPlaatsen=2
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        # add pages
        dp.add_page([None, "1", None])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=["101-cosmic-utensils"],
            properties=[],
            verkoopinrichting=[],
        )

        # pref
        dp.add_pref(erkenningsNummer="2", plaatsId="3", priority=1)

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(stands_erk("1", allocation), ["1"])
        try:
            reject_erk("2", allocation)
        except Exception as e:
            self.fail("merchant not found in rejections")


class TestRestrictedBranches(unittest.TestCase):
    """
    Een ondernemer in een beperkte branche (bijv. agf)
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 2,
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
            sollicitatieNummer="3",
            description="Terry Bozio",
            voorkeur={
                "branches": ["404-lost-and-found"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        # branches
        dp.add_branche(
            brancheId="101-cosmic-utensils", verplicht=True, maximumPlaatsen=1
        )

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        # add pages
        dp.add_page([None, "1", "2", "3", None])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=["101-cosmic-utensils"],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=["101-cosmic-utensils"],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=["101-cosmic-utensils"],
            properties=[],
            verkoopinrichting=[],
        )

        self.dp = dp

    def test_not_exceed_max_stands_if_soll(self):
        """
        kan het maximum aantal plaatsen als SOLL niet overschrijden
        """
        # Ondernemers in een branche met een toewijzingsbeperking kregen in sommige
        # situaties teveel plaatsen toegekend. Dit gebeurde voornamelijk als er nog
        # 1 brancheplek beschikbaar was maar de ondernemer aan zet wilde graag 2 plaatsen.
        # Als er vervolgens optimistisch werd ingedeeld kreeg deze ondernemer gelijk
        # 2 plaatsen, waarmee het maximum met 1 plaats werd overschreden.
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(stands_erk("1", allocation), ["1"])

    def test_may_exceed_max_if_vpl(self):
        """
        kan het maximum aantal plaatsen overschrijden indien VPL
        """
        # VPL in een branche met een toewijzingsbeperking moeten wel altijd hun
        # plaatsen toegewezen krijgen, ook al overschrijden ze daarmee het maximum.
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-cosmic-utensils"],
                "maximum": 2,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(stands_erk("1", allocation), ["1", "2"])
