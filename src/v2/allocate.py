import datetime
import json
import sys

from v2.markt import Markt
from v2.conf import KraamTypes, trace, PhaseValue
from v2.strategy import ReceiveOwnKramenStrategy, HierarchyStrategy, FillUpStrategyBList, OptimizationStrategy
from v2.validate import ValidateMarkt
from v2.parse import Parse


def allocate(markt_meta, rows, branches, ondernemers, *args, **kwargs):
    trace.set_phase(epic='initial', story='meta', task='time', group=PhaseValue.unknown, agent=PhaseValue.event)
    start = datetime.datetime.now()
    trace.log(f"start {start}")

    markt = Markt(markt_meta, rows, branches, ondernemers)
    ValidateMarkt(markt)

    trace.set_phase(epic='allocate_own_kramen', story='allocate_own_kramen')
    receive_own_kramen_strategy = ReceiveOwnKramenStrategy(markt)
    receive_own_kramen_strategy.run()

    trace.set_phase(epic='verplichte_branches')
    for branche in markt.verplichte_branches:
        trace.set_phase(story=branche.shortname)
        verplichte_branche_strategy = HierarchyStrategy(markt, branche=branche)

        verplichte_branche_strategy.run()
        fill_up_strategy_b_list = FillUpStrategyBList(markt, branche=branche)
        fill_up_strategy_b_list.run()
        markt.kramen.remove_verplichte_branche(branche=branche)
        markt.report_indeling()

    trace.set_phase(epic='kraamtypes')
    for kraam_type in KraamTypes.BAK, KraamTypes.BAK_LICHT, KraamTypes.EVI:
        trace.set_phase(story=kraam_type.value)
        bak_strategy = HierarchyStrategy(markt, kraam_type=kraam_type)
        bak_strategy.run()
        markt.kramen.remove_kraam_type(kraam_type=kraam_type)
        markt.report_indeling()

    trace.set_phase(epic='kraamtypes_reprise')
    markt.kramen.restore_original_kraamtype()
    markt.report_indeling()
    for kraam_type in KraamTypes.BAK, KraamTypes.BAK_LICHT, KraamTypes.EVI:
        trace.set_phase(story=kraam_type.value)
        bak_strategy = HierarchyStrategy(markt, kraam_type=kraam_type)
        bak_strategy.run()
        fill_up_strategy_b_list = FillUpStrategyBList(markt, kraam_type=kraam_type)
        fill_up_strategy_b_list.run()
        markt.kramen.remove_kraam_type(kraam_type=kraam_type)
        markt.report_indeling()

    trace.set_phase(epic='remaining', story='remaining')
    remaining_query = dict(kraam_type__not__in=[*KraamTypes], branche__not__in=markt.verplichte_branches)
    remaining_strategy = HierarchyStrategy(markt, **remaining_query)
    remaining_strategy.run()

    markt.report_ondernemers()
    markt.report_branches()
    trace.set_phase(epic='optimization')
    optimization_strategy = OptimizationStrategy(markt)
    optimization_strategy.run()

    trace.set_phase(epic='fill_up_b_list')
    fill_up_strategy_b_list = FillUpStrategyBList(markt, **remaining_query)
    fill_up_strategy_b_list.run()

    markt.report_ondernemers()
    markt.report_rejections()
    markt.report_branches()

    allocations, rejections = markt.get_allocations()
    output = {
        'toewijzingen': allocations,
        'afwijzingen': rejections,
    }

    trace.set_phase(epic='end', story='meta', task='time')
    trace.log(f"Allocation hash: {markt.kramen.calculate_custom_allocation_hash()}")
    stop = datetime.datetime.now()
    trace.log(f"{stop} - duration {stop - start}")
    return output


def parse_and_allocate(input_data):
    trace.clear()
    try:
        parsed = Parse(input_data)
        output = allocate(**parsed.__dict__)
    except Exception as e:
        output = {'error': str(e)}
    enriched_output = {
        **input_data,
        **output,
    }
    logs = trace.get_logs()
    return enriched_output, logs


if __name__ == '__main__':
    """
    Usage: allocate.py <input json (relative to src/v2 dir)> <path to tracefile>
    """
    _script, input_json_file, trace_file_path, *rest = sys.argv
    trace.local = True

    print(f"input_json_file: {input_json_file}, trace_file_path: {trace_file_path}")
    parsed = Parse(json_file=input_json_file)
    output = allocate(**parsed.__dict__)

    logs = trace.get_logs()
    json.dumps(logs)

    # trace.show()
    if trace_file_path:
        trace.save(trace_file_path)
