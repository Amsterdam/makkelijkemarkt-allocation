from v2.kramen import Kraam, KraamType
from v2.fixtures.optimization.branches import branches

branche_1, branche_2, branche_3, branche_4 = branches
kraam_type_bak = KraamType(bak=True)

rows = [
    [
        Kraam(id=1, ondernemer=None, branche=branche_1),
        Kraam(id=2, ondernemer=None, branche=None),
        Kraam(id=3, ondernemer=None, branche=None),
    ],
    [
        Kraam(id=4, ondernemer=None, branche=None),
        Kraam(id=5, ondernemer=None, branche=None),
        Kraam(id=6, ondernemer=None, branche=None),
        Kraam(id=7, ondernemer=None, branche=None),
    ],
    [
        Kraam(id=11, ondernemer=None, branche=None, bak=True),
        Kraam(id=12, ondernemer=None, branche=None, evi=True),
        Kraam(id=13, ondernemer=None, branche=None),
        Kraam(id=14, ondernemer=None, branche=None),
        Kraam(id=15, ondernemer=None, branche=None),
    ],
]
