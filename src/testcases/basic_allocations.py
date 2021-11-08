import unittest

class TestBasicAllocation(unittest.TestCase):
    """
    Een ondernemer die ingedeeld wil worden
    """

    def test_assign_empty_stand(self):
        """
        wordt toegewezen aan een lege plek
        """
        pass

    def test_assign_non_active_stands(self):
        """
        komt niet op een inactieve marktplaats
        """
        pass

    def test_assign_standwerker(self):
        """
        komt op een standwerkerplaats als hij standwerker is
        """
        pass

    def test_assign_unused_baking_stand(self):
        """
        komt op een bakplaats als deze niet gebruikt wordt
        """
        pass

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
