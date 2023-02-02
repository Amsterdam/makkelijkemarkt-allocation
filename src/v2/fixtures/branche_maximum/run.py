import json

from v2.allocate import allocate
from v2.conf import KraamTypes, trace
from v2.fixtures.branche_maximum.kramen import rows
from v2.fixtures.branche_maximum.branches import branches
from v2.fixtures.branche_maximum.ondernemers import ondernemers
from v2.fixtures.branche_maximum.markt import markt_meta


if __name__ == '__main__':
    trace.local = True
    output = allocate(markt_meta, rows, branches, ondernemers)
    logs = trace.get_logs()
    json.dumps(logs)

    # trace.show()
