import unittest
from kjk.allocation import Allocator
from kjk.inputdata import MockDataprovider
from pprint import pprint
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestSollAllocation(unittest.TestCase):
    """
    Een sollicitant die ingedeeld wil worden
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
                "branches": ["101-afg"],
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
            sollicitatieNummer="2",
            description="C Beefheart",
            voorkeur={
                "branches": ["101-afg"],
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
        dp.add_branche(brancheId="102-vis", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)
        dp.add_rsvp(erkenningsNummer="3", attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()

    def test_not_required_to_state_branch(self):
        """
        Een sollicitant die ingedeeld wil worden
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="2",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": ["eigen-materieel"],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_stand(
            plaatsId="4",
            branches=["102-vis"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        self.dp.add_stand(
            plaatsId="5",
            branches=["101-agf"],
            properties=[],
            verkoopinrichting=["eigen-materieel"],
        )
        self.dp.add_page(["1", "2", "4", "5"])
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        stds = alloc_erk("1", allocation)["plaatsen"]
        self.assertListEqual(stds, ["5"])

    def test_pref_evi_locations(self):
        """
        krijgt voorkeur op plaatsen zonder kraam indien zij een EVI hebben
        """
        pass

    def test_has_alist_pref(self):
        """
        krijgt voorkeur als zij op de A-lijst staan
        """
        pass

    def test_branche_pref_to_other_soll(self):
        """
        krijgt voorkeur over andere sollicitanten op een brancheplaats als zij in deze branche opereren
        """
        pass

    def test_pref_to_vpl_if_bracnhe(self):
        """
        krijgt voorkeur over VPLs op een brancheplaats als zij in deze branche opereren
        """
        pass

    def test_can_move_to_absent_vpl(self):
        """
        mag naar een plaats van een afwezige VPL
        """
        pass

    def test_will_not_go_to_pref_of_others(self):
        """
        komt liefst niet op de voorkeursplek van een ander als zij flexibel ingedeeld willen worden
        """
        pass

    def test_can_choose_to_only_want_prefs(self):
        """
        kan kiezen niet te worden ingedeeld op willekeurige plaatsen
        """
        pass
