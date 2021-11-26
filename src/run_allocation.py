import sys, traceback
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider
import time

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
