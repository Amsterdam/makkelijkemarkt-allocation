from v2.ondernemers import Ondernemer
from v2.conf import Status
from v2.fixtures.branche_maximum.branches import branches

branche_1, branche_2, branche_3, branche_4 = branches

vpls = [
    Ondernemer(rank=1, branche=branche_1, prefs=[7, 8], min=1, max=2, anywhere=True, status=Status.VPL, own=[1]),
    Ondernemer(rank=2, branche=branche_1, prefs=[], min=1, max=2, anywhere=False, status=Status.VPL, own=[2]),
]

ebs = [
]

sollicitanten = [
    Ondernemer(rank=101, branche=branche_1, prefs=[1], min=1, max=3, anywhere=True, status=Status.SOLL),
    Ondernemer(rank=102, branche=branche_1, prefs=[1], min=1, max=3, anywhere=True, status=Status.SOLL),
]

b_lijst = [
]

ondernemers = [*vpls, *ebs, *sollicitanten, *b_lijst]
