import json

from v2.allocate import allocate
from v2.conf import logger, KraamTypes, trace
from v2.fixtures.expand_after_move.kramen import rows
from v2.fixtures.expand_after_move.branches import branches
from v2.fixtures.expand_after_move.ondernemers import ondernemers
from v2.fixtures.expand_after_move.markt import markt_meta


if __name__ == '__main__':
    logger.local = True
    output = allocate(markt_meta, rows, branches, ondernemers)
    logs = logger.get_logs()
    json.dumps(logs)

    # trace.show()
