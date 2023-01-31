from v2.ondernemers import Ondernemer
from v2.conf import Status
from v2.fixtures.expand_after_move.branches import branches

branche_1, branche_2, branche_3, branche_4 = branches

vpls = [
    Ondernemer(rank=1, branche=None, prefs=[7, 8], min=1, max=3, anywhere=True, status=Status.VPL, own=[1, 2]),
    Ondernemer(rank=2, branche=None, prefs=[], min=1, max=3, anywhere=False, status=Status.VPL, own=[3]),
]

ebs = [
]

sollicitanten = [
    Ondernemer(rank=101, branche=None, prefs=[1], min=1, max=3, anywhere=False, status=Status.SOLL),
]

b_lijst = [
]

ondernemers = [*vpls, *ebs, *sollicitanten, *b_lijst]
