import json

from v2.allocate import allocate
from v2.conf import KraamTypes, trace
from v2.fixtures.default.kramen import rows
from v2.fixtures.default.branches import branches
from v2.fixtures.default.ondernemers import ondernemers
from v2.fixtures.default.markt import markt_meta


if __name__ == '__main__':
    trace.local = True
    output = allocate(markt_meta, rows, branches, ondernemers)
    logs = trace.get_logs()
    json.dumps(logs)

    # trace.show()
