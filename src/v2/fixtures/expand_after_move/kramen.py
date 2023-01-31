from v2.kramen import Kraam
from v2.fixtures.branches import branches

branche_1, branche_2, branche_3, branche_4 = branches

rows = [
    [
        Kraam(id=1, ondernemer=None, branche=branche_1),
        Kraam(id=2, ondernemer=None, branche=branche_1),
        Kraam(id=3, ondernemer=None, branche=None),
        Kraam(id=4, ondernemer=None, branche=branche_2),
        Kraam(id=5, ondernemer=None, branche=branche_2),
        Kraam(id=6, ondernemer=None, branche=branche_2),
    ],
    [
        Kraam(id=7, ondernemer=None, branche=None),
        Kraam(id=8, ondernemer=None, branche=None),
        Kraam(id=9, ondernemer=None, branche=None),
        Kraam(id=10, ondernemer=None, branche=None, bak=True),
        Kraam(id=11, ondernemer=None, branche=branche_3),
        Kraam(id=12, ondernemer=None, branche=branche_4),
        Kraam(id=13, ondernemer=None, branche=branche_4),
    ],
    [
        Kraam(id=14, ondernemer=None, branche=None, bak=True, evi=True),
        Kraam(id=15, ondernemer=None, branche=None, bak=True, evi=True),
    ],
    [
        Kraam(id=16, ondernemer=None, branche=branche_1),
        Kraam(id=17, ondernemer=None, branche=None),
        Kraam(id=18, ondernemer=None, branche=None),
        Kraam(id=19, ondernemer=None, branche=None),
    ],
    [
        Kraam(id=20, ondernemer=None, branche=branche_1),
        Kraam(id=21, ondernemer=None, branche=branche_1),
        Kraam(id=22, ondernemer=None, branche=branche_1),
        Kraam(id=23, ondernemer=None, branche=branche_1),
        Kraam(id=24, ondernemer=None, branche=branche_1, bak=True),
        Kraam(id=25, ondernemer=None, branche=branche_1),
        Kraam(id=26, ondernemer=None, branche=None, bak_licht=True),
        Kraam(id=27, ondernemer=None, branche=None, bak_licht=True),
        Kraam(id=28, ondernemer=None, branche=None, evi=True),
        Kraam(id=29, ondernemer=None, branche=None, evi=True),
        Kraam(id=30, ondernemer=None, branche=branche_3, bak=True),
    ],
]
