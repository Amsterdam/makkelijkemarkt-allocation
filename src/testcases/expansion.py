import unittest


class TestExpansion(unittest.TestCase):
    """
    Een ondernemer die wil uitbreiden
    """

    def test_stay_in_same_row(self):
        """
        blijft binnen dezelfde marktkraamrij
        """
        pass

    def test_can_have_second_stand(self):
        """
        kan een 2de plaats krijgen
        """
        pass

    def test_will_get_following_stands(self):
        """
        krijgt aaneensluitende plaatsen
        """
        pass

    def test_get_2_extra_if_space_sufficient(self):
        """
        krijgt gelijk twee plaatsen als er genoeg ruimte op de markt is
        """
        pass

    def test_more_tand_two_stands_must_wait(self):
        """
        naar meer dan 2 plaatsen moet wachten op iedereen die 2 plaatsen wil
        """
        pass

    def test_can_have_3_stands(self):
        """
        kan 3 plaatsen krijgen
        """
        pass

    def test_must_stay_in_branche_location(self):
        """
        kan niet uitbreiden naar een niet-branche plaats als zijn branche verplicht is
        """
        pass

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
