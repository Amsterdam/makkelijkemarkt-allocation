import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider
from kjk.test_utils import alloc_erk, stands_erk, reject_erk, print_alloc


class TestSollExpandNonFlex(unittest.TestCase):
    """
    Flexibel indelen geldt alleen voor eerste toewijzing, niet uitbreidingsslots.
    """

    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        dp.add_merchant(
            erkenningsNummer="1",
            plaatsen=[],
            status="soll",
            sollicitatieNummer="1",
            description="frank zappa",
            voorkeur={
                "branches": [],
                "maximum": 3,
                "minimum": 1,
                "anywhere": False,
                "verkoopinrichting": [],
                "absentFrom": "",
                "absentUntil": "",
            },
        )

        dp.add_pref(erkenningsNummer="1", plaatsId="3", priority=0)

        dp.add_rsvp(erkenningsNummer="1", attending=True)

        dp.set_alist([{"erkenningsNummer": "1"}])

        dp.add_page(["1", "2", "3", "4", "5"])

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
        )
        dp.add_stand(
            plaatsId="4",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )
        dp.add_stand(
            plaatsId="5",
            branches=[],
            properties=[],
            verkoopinrichting=[],
        )

        self.dp = dp

    def test_uitbreiding_niet_afgewezen_buiten_pref(self):
        """
        Als toegewezen plekken buiten voorkeursplekken vallen wordt er niet afgewezen
        """
        self.dp.mock()
        allocator = Allocator(self.dp)
        allocation = allocator.get_allocation()

        stands = stands_erk("1", allocation)

        self.assertSetEqual(set(stands), {"1", "2", "3"})
