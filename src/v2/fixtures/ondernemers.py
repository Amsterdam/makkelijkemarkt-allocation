from v2.ondernemers import Ondernemer
from v2.conf import Status
from v2.fixtures.branches import branches

branche_1, branche_2, branche_3, branche_4 = branches

vpls = [
    Ondernemer(rank=1, branche=branche_1, prefs=[16, 4, 5], min=1, max=3, anywhere=True, status=Status.VPL, own=[6]),
    Ondernemer(rank=2, branche=branche_2, prefs=[7, 3, 5], min=1, max=3, anywhere=False, status=Status.VPL, own=[5]),
    Ondernemer(rank=3, branche=branche_3, prefs=[10, 11], min=1, max=2, anywhere=False, status=Status.VPL, own=[3, 4]),
    Ondernemer(rank=4, branche=branche_1, prefs=[12, 18, 19], min=1, max=4, anywhere=False, status=Status.TVPL, own=[24]),
    Ondernemer(rank=5, branche=branche_2, prefs=[20, 9], min=1, max=3, anywhere=True, status=Status.TVPLZ, own=['tvplz1']),
    Ondernemer(rank=6, branche=branche_1, prefs=[20, 21, 22], min=1, max=2, anywhere=True, status=Status.TVPL, own=[20]),
]

ebs = [
    Ondernemer(rank=21, branche=branche_1, prefs=[21, 22, 23], min=1, max=3, anywhere=False, status=Status.EB, own=[22]),
    Ondernemer(rank=22, branche=branche_2, prefs=[27, 28], min=1, max=3, anywhere=False, status=Status.EB, own=[27]),
]

sollicitanten = [
    Ondernemer(rank=101, branche=branche_1, prefs=[1, 4, 2, 3], min=1, max=3, anywhere=False, status=Status.SOLL),
    Ondernemer(rank=102, branche=branche_1, prefs=[20, 3], min=1, max=3, anywhere=True, status=Status.SOLL),
    Ondernemer(rank=120, branche=branche_2, prefs=[5, 6], min=1, max=1, anywhere=True, status=Status.SOLL),
    Ondernemer(rank=130, prefs=[6, 7], min=1, max=2, anywhere=True, status=Status.SOLL),
    Ondernemer(rank=140, branche=branche_4, prefs=[8, 9], min=2, max=4, anywhere=False, status=Status.SOLL,
               bak_licht=True),
    Ondernemer(rank=150, branche=branche_4, prefs=[13, 20], min=1, max=4, anywhere=True, status=Status.SOLL,
               bak=True, evi=True),
    Ondernemer(rank=160, branche=branche_4, prefs=[1, 2], min=1, max=4, anywhere=True, status=Status.SOLL,
               bak_licht=True, evi=True),
    Ondernemer(rank=170, branche=branche_4, prefs=[3, 4], min=1, max=4, anywhere=True, status=Status.SOLL,
               evi=True),
]

b_lijst = [
    Ondernemer(rank=201, branche=branche_1, prefs=[4], min=1, max=3, anywhere=True, status=Status.B_LIST),
    Ondernemer(rank=202, branche=branche_1, prefs=[4], min=1, max=3, anywhere=True, status=Status.B_LIST),
    Ondernemer(rank=220, branche=branche_2, prefs=[10, 18], min=1, max=1, anywhere=True, status=Status.B_LIST),
    Ondernemer(rank=230, branche=branche_3, prefs=[17], min=1, max=2, anywhere=True, status=Status.B_LIST,
               bak=True),
    Ondernemer(rank=240, branche=branche_4, prefs=[20], min=1, max=1, anywhere=True, status=Status.B_LIST,
               bak_licht=True),
]

ondernemers = [*vpls, *ebs, *sollicitanten, *b_lijst]
