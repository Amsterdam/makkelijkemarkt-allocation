import unittest


class TestSollAllocation(unittest.TestCase):
    """
    Een sollicitant die ingedeeld wil worden
    """

    def test_not_required_to_state_branch(self):
        """
        Een sollicitant die ingedeeld wil worden
        """
        pass

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
