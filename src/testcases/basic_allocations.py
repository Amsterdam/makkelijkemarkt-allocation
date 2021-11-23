import unittest
from pprint import pprint
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider, MockDataprovider

class TestBasicAllocation(unittest.TestCase):
    """
    Een ondernemer die ingedeeld wil worden
    """
    def setUp(self):
        dp = MockDataprovider("../fixtures/test_input.json")

        # merchants
        dp.add_merchant(erkenningsNummer='1',
                        plaatsen=['1', '2'],
                        status='vpl',
                        sollicitatieNummer="2",
                        description='Frank Zappa',
                        voorkeur={"branches": ['101-afg'], "maximum": 2, "minimum": 2, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        dp.add_merchant(erkenningsNummer='2',
                        plaatsen=[],
                        status='soll',
                        sollicitatieNummer="2",
                        description='C Beefheart',
                        voorkeur={"branches": ['101-afg'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        dp.add_merchant(erkenningsNummer='3',
                        plaatsen=[],
                        status='soll',
                        sollicitatieNummer="3",
                        description='J Medeski',
                        voorkeur={"branches": ['mooie spullen'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        # stands
        dp.add_stand(plaatsId='1', branches=['101-agf'], properties=['boom'], verkoopinrichting=[])
        dp.add_stand(plaatsId='2', branches=['101-agf'], properties=['boom'], verkoopinrichting=[])
        dp.add_stand(plaatsId='3', branches=['101-agf'], properties=['boom'], verkoopinrichting=[], inactive=True)

        # branches
        dp.add_branche(brancheId="101-agf", verplicht=True, maximumPlaatsen=12)

        # rsvp
        dp.add_rsvp(erkenningsNummer='1', attending=True)
        dp.add_rsvp(erkenningsNummer='2', attending=True)
        dp.add_rsvp(erkenningsNummer='3', attending=True)

        self.dp = dp
        dp.mock()
        allocator = Allocator(dp)
        self.market_allocation = allocation = allocator.get_allocation()


    def test_assign_empty_stand(self):
        """
        wordt toegewezen aan een lege plek
        """
        stands = self.market_allocation['toewijzingen']
        self.assertEqual(len(stands), 1)

    def test_assign_non_active_stands(self):
        """
        komt niet op een inactieve marktplaats
        """
        stands = self.market_allocation['toewijzingen']
        for st in stands:
            pl = st['plaatsen']
            self.assertNotIn(3, pl)

    def test_assign_standwerker(self):
        """
        komt op een standwerkerplaats als hij standwerker is
        """
        # exp merchants apperently have stands
        # so they will always be allocated to their stands
        self.dp.add_merchant(erkenningsNummer='4',
                             #plaatsen=['66'],
                             #status='soll',
                             plaatsen=[],
                             status='soll',
                             sollicitatieNummer="4",
                             description='Janus Standwerker',
                             voorkeur={"branches": ['401-experimentele-zone'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        self.dp.add_rsvp(erkenningsNummer='4', attending=True)
        self.dp.add_stand(plaatsId='66', branches=['401-experimentele-zone'], properties=[], verkoopinrichting=[], inactive=False)
        self.dp.add_branche(brancheId="401-experimentele-zone", verplicht=True, maximumPlaatsen=12)
        self.dp.mock()

        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        for tw in market_allocation['toewijzingen']:
            if tw['plaatsen'][0] == '66':
                self.assertEqual("Janus Standwerker", tw['ondernemer']['description'])

    def test_assign_unused_baking_stand(self):
        """
        komt op een bakplaats als deze niet gebruikt wordt
        """
        self.dp.add_merchant(erkenningsNummer='244',
                             plaatsen=[],
                             status='soll',
                             sollicitatieNummer="6",
                             description='K. Oopman',
                             voorkeur={"branches": ['handel'], "maximum": 1, "minimum": 1, "verkoopinrichting":[], "absentFrom":"", "absentUntil": ""})

        self.dp.add_rsvp(erkenningsNummer='244', attending=True)
        self.dp.add_stand(plaatsId='66', branches=['bak'], properties=[], verkoopinrichting=[], inactive=False)
        self.dp.add_branche(brancheId="bak", verplicht=True, maximumPlaatsen=12)
        self.dp.mock()

        allocator = Allocator(self.dp)
        market_allocation = allocator.get_allocation()
        for tw in market_allocation['toewijzingen']:
            print(tw['erkenningsNummer'], " : ", tw['plaatsen'])

    def test_assign_unused_evi_stand(self):
        """
        komt op een EVI plaats als deze niet gebruikt wordt
        """
        pass

    def test_assign_rejected_stand(self):
        """
        komt op de plek van een afgewezen ondernemer, na een afwijzing wegens te weinig ruimte
        """
        pass
