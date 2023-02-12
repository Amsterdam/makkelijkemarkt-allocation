from v2.ondernemers import Ondernemer
from v2.conf import Status
from v2.fixtures.optimization.branches import branches

branche_1, branche_2, branche_3, branche_4 = branches

vpls = [
    Ondernemer(rank=1, branche=branche_3, prefs=[], min=1, max=1, anywhere=True, status=Status.VPL, own=[1]),
    Ondernemer(rank=2, branche=branche_1, prefs=[], min=1, max=2, anywhere=False, status=Status.VPL, own=[2]),
    Ondernemer(rank=3, branche=branche_2, prefs=[], min=1, max=2, anywhere=False, status=Status.VPL, own=[4]),
    Ondernemer(rank=4, branche=branche_2, prefs=[], min=1, max=2, anywhere=False, status=Status.VPL, own=[6]),
]

ebs = [
]


soll_103 = Ondernemer(rank=103, branche=branche_2, prefs=[], min=1, max=3, anywhere=True, status=Status.SOLL)
soll_104 = Ondernemer(rank=104, branche=branche_2, prefs=[], min=1, max=3, anywhere=True, status=Status.SOLL)
soll_105 = Ondernemer(rank=105, branche=branche_2, prefs=[], min=1, max=3, anywhere=True, status=Status.SOLL)

sollicitanten = [
    Ondernemer(rank=101, branche=branche_3, prefs=[], min=1, max=1, anywhere=True, status=Status.SOLL),
    Ondernemer(rank=102, branche=branche_4, prefs=[], min=1, max=3, anywhere=True, status=Status.SOLL, bak=True),
    soll_103,
    soll_104,
    soll_105,
]

b_lijst = [
]

ondernemers = [*vpls, *ebs, *sollicitanten, *b_lijst]
