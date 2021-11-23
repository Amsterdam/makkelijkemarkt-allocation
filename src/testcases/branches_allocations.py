import unittest


class TestRequiredBranches(unittest.TestCase):
    """
    Een ondernemer in een verplichte branche (bijv. bak)
    """

    def test_required_branche_stand(self):
        """
        kan enkel op een brancheplek staan
        """
        pass

    def test_assign_most_suitable_stand(self):
        """
        komt op de meest geschikte brancheplaats te staan
        """
        # Branche overlap is belangrijker dan de prioritering van de ondernemer.
        pass

    def test_can_not_axpand_to_non_branche_stand(self):
        """
        kan niet uitbreiden naar een niet-branche plaats
        """
        pass

    def test_reject_if_branche_stands_unavailable(self):
        """
        wordt afgewezen als er geen brancheplaatsen meer beschikbaar zijn
        """
        pass

    def test_reject_if_max_branches_reached(self):
        """
        wordt afgewezen als het maximum aantal branche-ondernemers bereikt is
        """
        pass

    def test_pref_vpl_moving(self):
        """
        krijgt voorrang boven VPLs die willen verplaatsen
        """
        pass

    def test_pref_to_soll_in_non_required_branches(self):
        """
        krijgt voorrang boven sollicitanten niet in een verplichte branche
        """
        # Altijd eerst brancheplaatsen proberen vullen met branche ondernemers.
        pass
    
class TestRestrictedBranches(unittest.TestCase):
    """
    Een ondernemer in een beperkte branche (bijv. agf)
    """

    def test_not_exceed_max_stands_if_soll(self):
        """
        kan het maximum aantal plaatsen als SOLL niet overschrijden
        """
        # Ondernemers in een branche met een toewijzingsbeperking kregen in sommige
        # situaties teveel plaatsen toegekend. Dit gebeurde voornamelijk als er nog
        # 1 brancheplek beschikbaar was maar de ondernemer aan zet wilde graag 2 plaatsen.
        # Als er vervolgens optimistisch werd ingedeeld kreeg deze ondernemer gelijk
        # 2 plaatsen, waarmee het maximum met 1 plaats werd overschreden.
        pass

    def test_may_exceed_max_if_vpl(self):
        """
        kan het maximum aantal plaatsen overschrijden indien VPL
        """
        # VPL in een branche met een toewijzingsbeperking moeten wel altijd hun
        # plaatsen toegewezen krijgen, ook al overschrijden ze daarmee het maximum.
        pass

    def test_allocation_strategy_required_branche(self):
        """
        kan conservatief ingedeeld worden terwijl de rest van de markt optimistisch ingedeeld wordt
        """
        pass
