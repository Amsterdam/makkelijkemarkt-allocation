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
            sollicitatieNummer="92",
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
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_stand(
            plaatsId="4",
            branches=["102-vis"],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_stand(
            plaatsId="5",
            branches=["101-agf"],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_page(["1", "2", "4", "5"])
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(stands_erk("1", allocation), ["2"])

    def test_pref_evi_locations(self):
        """
        krijgt voorkeur op plaatsen zonder kraam indien zij een EVI hebben
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="5",
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
        self.dp.add_merchant(
            erkenningsNummer="4",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="4",
            description="Y Medeski",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="5",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="1",
            description="Z Medeski",
            voorkeur={
                "branches": ["mooie spullen"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_rsvp(erkenningsNummer="4", attending=True)
        self.dp.add_rsvp(erkenningsNummer="5", attending=True)

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
        self.assertListEqual(stands_erk("1", allocation), ["5"])

    def test_has_alist_pref(self):
        """
        krijgt voorkeur als zij op de A-lijst staan
        """
        self.dp.update_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="9",
            description="Frank Zappa",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="4",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="6",
            description="Y Medeski",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )
        self.dp.add_merchant(
            erkenningsNummer="5",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="7",
            description="Z Medeski",
            voorkeur={
                "branches": ["101-agf"],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        self.dp.add_rsvp(erkenningsNummer="4", attending=True)
        self.dp.add_rsvp(erkenningsNummer="5", attending=True)

        self.dp.add_stand(
            plaatsId="4",
            branches=["102-vis"],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_stand(
            plaatsId="5",
            branches=["101-agf"],
            properties=[],
            verkoopinrichting=[],
        )
        self.dp.add_page(["1", "2", "4", "5"])
        self.dp.set_alist([{"erkenningsNummer": "1"}])
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(stands_erk("1", allocation), ["1"])

    def test_branche_pref_to_other_soll(self):
        """
        krijgt voorkeur over andere sollicitanten op een brancheplaats als zij in deze branche opereren
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="44",
            description="Frank Zappa",
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
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="9",
            description="C Beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page(["1"])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("1", allocation)["plaatsen"], ["1"])
        reject_erk("2", allocation)

    def test_pref_to_vpl_if_branche(self):
        """
        krijgt voorkeur over VPLs op een brancheplaats als zij in deze branche opereren
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="44",
            description="Frank Zappa",
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
            erkenningsNummer="2",
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="9",
            description="C Beefheart",
            voorkeur={
                "branches": ["autobanden"],
                "maximum": 3,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page(["1", "2", "3"])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        dp.set_alist([{"erkenningsNummer": "1"}])

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("1", allocation)["plaatsen"], ["3"])

    def test_can_move_to_absent_vpl(self):
        """
        mag naar een plaats van een afwezige VPL
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="44",
            description="Frank Zappa",
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
            plaatsen=["1", "2"],
            status="vpl",
            sollicitatieNummer="9",
            description="C Beefheart",
            voorkeur={
                "branches": [],
                "maximum": 3,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page(["1", "2", "3"])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=False)

        # prefs soll wants stand 1
        dp.add_pref(erkenningsNummer="1", plaatsId="1", priority=1)

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        self.assertListEqual(alloc_erk("1", allocation)["plaatsen"], ["1"])

    def test_will_not_go_to_pref_of_others(self):
        """
        komt liefst niet op de voorkeursplek van een ander als zij flexibel ingedeeld willen worden
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=44,
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=[],
            status="soll",
            sollicitatieNummer=9,
            description="C Beefheart",
            voorkeur={
                "branches": [],
                "maximum": 1,
                "minimum": 1,
                "anywhere": True,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page(["1", "2", "3"])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        # prefs soll wants stand 1
        dp.add_pref(erkenningsNummer="1", plaatsId="1", priority=1)

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        # normally Beefheart would get number 1
        # zappa gets number 1 because pref and Beefheart does not care
        self.assertListEqual(alloc_erk("1", allocation)["plaatsen"], ["1"])

        # add competing pref
        dp.add_pref(erkenningsNummer="2", plaatsId="1", priority=1)

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        # now beefheart gets one he has also pref and better rating (lower sollicitatieNummer)
        self.assertListEqual(alloc_erk("2", allocation)["plaatsen"], ["1"])

    def test_can_choose_to_only_want_prefs(self):
        """
        kan kiezen niet te worden ingedeeld op willekeurige plaatsen
        """
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="44",
            description="Frank Zappa",
            voorkeur={
                "branches": [],
                "maximum": 3,
                "minimum": 3,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_merchant(
            erkenningsNummer="2",
            plaatsen=["1"],
            status="vpl",
            sollicitatieNummer="9",
            description="C Beefheart",
            voorkeur={
                "branches": [],
                "maximum": 3,
                "minimum": 2,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_page(["1", "2", "3"])

        # stands
        dp.add_stand(
            plaatsId="1",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="2",
            branches=[],
            properties=["boom"],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="3",
            branches=["101-agf"],
            properties=["boom"],
            verkoopinrichting=[],
        )

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer="1", attending=True)
        dp.add_rsvp(erkenningsNummer="2", attending=True)

        # prefs soll wants stand 1
        dp.add_pref(erkenningsNummer="2", plaatsId="1", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="2", priority=1)
        dp.add_pref(erkenningsNummer="2", plaatsId="3", priority=1)

        dp.mock()
        allocator = Allocator(dp)
        allocation = allocator.get_allocation()
        self.assertEqual(
            reject_erk("1", allocation)["ondernemer"]["description"], "Frank Zappa"
        )
