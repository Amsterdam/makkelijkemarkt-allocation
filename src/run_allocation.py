from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider

try:
    dp = FixtureDataprovider("../fixtures/dapp_20211030/a_input.json")
    a = Allocator(dp)
    output = a.get_allocation()
except Exception as e:
    print("Error: ", e)
