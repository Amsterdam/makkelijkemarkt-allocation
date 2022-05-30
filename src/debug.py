from kjk.allocation import Allocator
from kjk import allocation
from kjk.inputdata import FixtureDataprovider
from kjk.utils import AllocationDebugger

allocation.DEBUG = True

dp = FixtureDataprovider("/home/johan/Desktop/eb-bak-zwaar_5.json")
allocator = Allocator(dp)
allocator.get_allocation()


# uncomment if needed:

# debug_data = allocator.get_debug_data()
# db = AllocationDebugger(allocator.get_debug_data())
# phase = db.get_allocation_phase_for_merchant("1990030703")
# print(phase)
# phase = db.get_allocation_phase_for_stand('14')
# print(phase)
