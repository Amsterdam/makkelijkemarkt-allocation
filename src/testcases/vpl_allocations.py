import unittest

class TestTVPallocation(unittest.TestCase):
    """
    Een VPL/TVPL die ingedeeld wil worden    
    """

    def test_pref_vpl_to_soll(self):
        """
        krijgt voorkeur boven sollicitanten
        """
        pass

    def test_allocation_fixed_stands(self):
        """
        wordt toegewezen aan zijn vaste plaats(en)
        """
        # Dit scenario laat expres 1 plaats vrij om een regression bug
        # in `calcSizes` te voorkomen (`size` werd daar verkeerd
        # berekend als er meer dan genoeg plaatsen waren).
        pass

    def test_vpl_max_stands(self):
        """
        kan zijn aantal vaste plaatsen verkleinen door een maximum in te stellen
        """
        pass

    def test_vpl_fixed_not_available(self):
        """
        wordt afgewezen als zijn vaste plaatsen niet beschikbaar zijn
        """
        pass

    def test_other_stands_if_not_available(self):
        """
        kan hetzelfde aantal willekeurige plaatsen krijgen als zijn eigen plaatsen niet beschikbaar zijn
        """
        # Uitgezet, omdat nog niet besloten is hoe om te gaan met 'willekeurig indelen' voor VPL.
        pass


class TestTVPLZallocation(unittest.TestCase):
    """
    Een TVPLZ die ingedeeld wil worden
    """

    def test_tvplz_must_register(self):
        """
        moet zich eerst expliciet aanmelden
        """
        pass
    
    def test_pref_to_soll(self):
        """
        krijgt voorkeur boven sollicitanten
        """
        pass

    def test_non_pref_to_evi_and_brache(self):
        """
        heeft geen voorrang over verplichte branche- en EVI ondernemers
        """
        pass

    def test_right_to_number_of_stands(self):
        """
        heeft recht op een vast aantal plaatsen, maar heeft geen vaste plaats(en)
        """
        pass

    def test_can_not_limit_stands(self):
        """
        mag zijn vaste aantal plaatsen niet verkleinen
        """
        pass

    def test_can_expand_stands(self):
        """
        mag zijn vaste aantal plaatsen uitbreiden indien mogelijk
        """
        pass
