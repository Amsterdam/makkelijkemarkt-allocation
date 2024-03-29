import datetime
import json
import sys

from v2.allocations.vpl import VplAllocation
from v2.markt import Markt
from v2.conf import KraamTypes, trace, PhaseValue, Status
from v2.strategy import ReceiveOwnKramenStrategy, HierarchyStrategy, FillUpStrategyBList, OptimizationStrategy
from v2.validate import ValidateMarkt

from v2.fixtures.optimization.kramen import rows, branche_3, kraam_type_bak
from v2.fixtures.optimization.branches import branches
from v2.fixtures.optimization.ondernemers import ondernemers, soll_103, soll_104, soll_105
from v2.fixtures.optimization.markt import markt_meta


if __name__ == '__main__':
    trace.local = True
    trace.set_phase(epic='initial', story='meta', task='time', group=PhaseValue.unknown, agent=PhaseValue.event)
    start = datetime.datetime.now()
    trace.log(f"start {start}")

    markt = Markt(markt_meta, rows, branches, ondernemers)
    ValidateMarkt(markt)

    trace.set_phase(epic='allocate_own_kramen', story='allocate_own_kramen')
    receive_own_kramen_strategy = ReceiveOwnKramenStrategy(markt)
    receive_own_kramen_strategy.run()

    trace.set_phase(epic='fixtures', story='fixtures', task='allocate_kramen',
                    group=Status.SOLL, agent=PhaseValue.event)
    markt.kramen.kramen_map[3].assign(soll_103)
    markt.kramen.kramen_map[5].assign(soll_104)
    markt.kramen.kramen_map[7].assign(soll_105)
    markt.report_indeling()

    vpl_allocation = VplAllocation(markt)
    vpl_allocation.vph_uitbreiding(vph_status=Status.VPL)
    # VPL uitbreiding should not be possible, all VPL uitbreiding blocked by SOLL
    markt.report_indeling()

    trace.set_phase(epic='optimization', story='optimization')
    optimization_strategy = OptimizationStrategy(markt)
    optimization_strategy.maximize_all_vph_expansion()

    assert markt.kramen.kramen_map[2].ondernemer == 2
    assert markt.kramen.kramen_map[3].ondernemer == 2
    assert markt.kramen.kramen_map[4].ondernemer == 3
    assert markt.kramen.kramen_map[5].ondernemer == 3
    assert markt.kramen.kramen_map[6].ondernemer == 4
    assert markt.kramen.kramen_map[7].ondernemer == 4

    # markt.kramen.kramen_map[4].branche = branche_3
    # markt.kramen.kramen_map[5].branche = branche_3
    # markt.kramen.kramen_map[7].branche = branche_3
    # markt.kramen.kramen_map[7].kraam_type = kraam_type_bak

    optimization_strategy.swap_ondernemers()
    assert markt.kramen.kramen_map[4].ondernemer == 4
    assert markt.kramen.kramen_map[5].ondernemer == 4
    assert markt.kramen.kramen_map[6].ondernemer == 3
    assert markt.kramen.kramen_map[7].ondernemer == 3
