import unittest


class TestRejections(unittest.TestCase):
    """
    Een ondernemer wordt afgewezen
    """

    def test_market_full_rejection(self):
        """
        als de markt vol is
        """
        pass


class TestVPLcancellation(unittest.TestCase):
    """
    Een VPL/TVPL die niet ingedeeld wil worden
    """

    def test_cancellation(self):
        """
        kan zich afmelden voor een marktdag
        """
        pass

    def test_periodic_cancellation(self):
        """
        kan zijn aanwezigheid voor een bepaalde periode uitschakelen
        """
        pass


class TestTVPLcancellation(unittest.TestCase):
    """
    Een TVPLZ die niet ingedeeld wil worden
    """

    def test_register_tvpl(self):
        """
        hoeft zich niet af te melden als zij zichzelf niet aangemeld hebben        
        """
        pass


class Test_SOLL_EXP_EXPF(unittest.TestCase):
    """
    Een sollicitant met een tijdelijke vaste plaats (exp of expf)
    """

    def test_must_register(self):
        """
        moet zich aanmelden als aanwezig om ingedeeld te worden
        """
        pass

    def test_allocated_before_other_soll(self):
        """
        wordt ingedeeld voor andere sollicitanten
        """
        pass

    def test_can_not_move_if_fixed_stand(self):
        """
        kan niet verplaatsen als zij een vaste plaats hebben
        """
        pass

    def test_can_not_have_min_pref(self):
        """
        kan geen minimum gewenste plaatsen opgeven in hun voorkeuren
        """
        pass


    def test_can_not_have_max_pref(self):
        """
        kan geen maximum aantal gewenste plaatsen opgeven in hun voorkeuren
        """
        pass


class TestMinimizeRejections(unittest.TestCase):
    """
    Minimaliseer het aantal afwijzingen
    """

    def test_competing_min_pref(self):
        """
        bij concurrerende minimum voorkeuren
        """
        pass

    def test_rejection_for_branches(self):
        """
        bij de 2de verplichte branche ondernemer als de 1ste wordt afgewezen
        """
        pass
