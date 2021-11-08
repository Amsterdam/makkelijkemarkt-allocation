import unittest


class TestEVI(unittest.TestCase):
    """ 
    Een ondernemer met een EVI
    """

    def test_can_only_be_at_evi_stand(self):
        """
        kan enkel op een EVI plaats staan
        """
        pass

    def test_most_suitable_stand(self):
        """
        komt op de meest geschikte EVI plaats te staan
        """
        # Branche overlap is hier belangrijker dan de prioritering van de ondernemer.
        pass
	
    def test_can_not_expand_to_non_evi_stand(self):
        """
        kan niet uitbreiden naar een niet-EVI plaats
        """
        pass

    def test_reject_if_no_more_evi_stands(self):
        """
        wordt afgewezen als er geen EVI plaatsen meer beschikbaar zijn
        """
        pass

    def test_pref_to_moving_vpl(self):
        """
        krijgt voorrang boven VPLs die willen verplaatsen
        """
        pass

    def test_pref_to_soll_no_evi(self):
        """
        krijgt voorrang boven sollicitanten zonder EVI
        """
        # Altijd eerst EVI plaatsen proberen vullen met EVI ondernemers.
        # Ook indien `strategy === 'conservative'`.
        pass
