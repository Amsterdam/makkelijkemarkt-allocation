"""
pass DEBUG as parameter to get debug logging when running tests
"""
import logging
import sys
import unittest

# market scenario tests
from testcases.basic_allocations import *
from testcases.alist_allocations import *
from testcases.vpl_allocations import *
from testcases.branches_allocations import *
from testcases.evi import *
from testcases.moving_vpl import *
from testcases.soll import *
from testcases.expansion import *
from testcases.misc import *
from testcases.dapper import *
from testcases.avoid_pref_by_sollnr import *
from testcases.baklicht import *
from testcases.art_312_lid_2 import *
from testcases.bug_fixes import *
from testcases.eb_expansion_pref import *
from testcases.crash import *
from testcases.bug_50364_soll_does_not_get_2_stands import *

from testcases.bug_Markt133 import *
from testcases.soll_expand_nonFlex import *

# unit-test
from test_allocation import *

DEBUG = "DEBUG"

if __name__ == "__main__":
    from kjk.logging import *

    if DEBUG not in sys.argv:
        logging.disable(logging.CRITICAL)
        clog.disabled = True
        log.disabled = True
    else:
        sys.argv = [arg for arg in sys.argv if arg != DEBUG]
        clog.set_level(logging.DEBUG)

    unittest.main()

    clog.disabled = False
    log.disabled = False
    logging.disable(logging.NOTSET)
