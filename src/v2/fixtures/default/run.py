import json

from v2.allocate import allocate
from v2.conf import logger, KraamTypes, trace
from v2.fixtures.default.kramen import rows
from v2.fixtures.default.branches import branches
from v2.fixtures.default.ondernemers import ondernemers
from v2.fixtures.default.markt import markt_meta


if __name__ == '__main__':
    logger.local = True
    output = allocate(markt_meta, rows, branches, ondernemers)
    logs = logger.get_logs()
    json.dumps(logs)
    print(logs)

    # trace.show()
