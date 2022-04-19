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

from testcases.bug_fixes import *

# unit-test
from test_allocation import *

if __name__ == "__main__":
    from kjk.logging import *

    logging.disable(logging.CRITICAL)
    clog.disabled = True
    log.disabled = True

    unittest.main()

    clog.disabled = False
    log.disabled = False
    logging.disable(logging.NOTSET)
