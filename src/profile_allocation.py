import traceback
import sys
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider
import time

import cProfile, pstats, io
from pstats import SortKey

pr = cProfile.Profile()
pr.enable()

try:
    start = time.time()
    dp = FixtureDataprovider("../fixtures/dapp_20211030/a_input.json")
    a = Allocator(dp)
    output = a.get_allocation()
    stop = time.time()
    print("Allocation completed in ", round(stop - start, 2), "sec")
except Exception as e:
    print("Error: ", e)
    print("-" * 60)
    traceback.print_exc(file=sys.stdout)
    print("-" * 60)

pr.disable()
s = io.StringIO()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print(s.getvalue())
