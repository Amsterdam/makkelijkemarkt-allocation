import unittest


class TestMovingVPL(unittest.TestCase):
    """
    Een VPL die wil verplaatsen
    """

    def test_pref_no_non_baking(self):
        """
        krijgt WEL voorrang boven sollicitanten die niet willen bakken
        krijgt WEL voorrang boven bak ondernemers als zij zelf ook bakken
        krijgt WEL voorrang boven EVI ondernemers als zij zelf ook een EVI hebben
        krijgt GEEN voorrang boven EVI ondernemers
        """
        pass

    def test_can_move_free_stand(self):
        """
        kan altijd verplaatsen naar een losse plaats
        """
        pass

    def test_can_not_take_other_vpl_stand(self):
        """
        mag niet naar een plaats van een andere aanwezige VPL
        """
        pass

    def test_can_switch_stands(self):
        """
        mag ruilen met een andere VPL
        """
        pass

    def test_can_take_stand_from_moved_vpl(self):
        """
        kan de plaats van een andere VPL krijgen als die ook verplaatst
        """
        pass

    def test_will_not_move_if_better_moving_vpl(self):
        """
        blijft staan als een VPL met hogere ancienniteit dezelfde voorkeur heeft
        """
        pass

    def test_can_move_to_stand_based_on_one_pref(self):
        """
        kan naar een locatie met minimaal 1 beschikbare voorkeur
        """
        pass

    def test_keep_number_of_stand(self):
        """
        met meerdere plaatsen behoudt dit aantal na verplaatsing
        """
        pass

    def test_keep_stands_if_prefs_not_available(self):
        """
        raken hun eigen plaats niet kwijt als hun voorkeur niet beschikbaar is
        """
        pass
