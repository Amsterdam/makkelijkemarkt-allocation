import datetime
import json
import sys

from v2.markt import Markt
from v2.conf import KraamTypes, trace
from v2.strategy import ReceiveOwnKramenStrategy, HierarchyStrategy, FillUpStrategyBList
from v2.validate import ValidateMarkt
from v2.parse import Parse


def allocate(markt_meta, rows, branches, ondernemers, *args, **kwargs):
    start = datetime.datetime.now()
    trace.log(f"start {start}")

    markt = Markt(markt_meta, rows, branches, ondernemers)
    ValidateMarkt(markt)

    receive_own_kramen_strategy = ReceiveOwnKramenStrategy(markt)
    receive_own_kramen_strategy.run()

    verplichte_branches = markt.get_verplichte_branches()
    for branche in verplichte_branches:
        trace.log(f'\n======> VERPLICHTE BRANCHE {branche}')
        verplichte_branche_strategy = HierarchyStrategy(markt, f'verplichte_branche_hierarchy {branche}',
                                                        branche=branche)
        verplichte_branche_strategy.run()
        trace.log('\n==> FILL UP')
        fill_up_strategy_b_list = FillUpStrategyBList(markt, f'verplichte_branche_fill_up_b {branche}', branche=branche)
        fill_up_strategy_b_list.run()
        markt.kramen.remove_verplichte_branche(branche=branche)
        markt.report_indeling()

    for kraam_type in KraamTypes.BAK, KraamTypes.BAK_LICHT, KraamTypes.EVI:
        trace.log(f'\n======> Kraam type: {kraam_type}')
        bak_strategy = HierarchyStrategy(markt, f'{kraam_type} hierarchy', kraam_type=kraam_type)
        bak_strategy.run()
        fill_up_strategy_b_list = FillUpStrategyBList(markt, f'{kraam_type} fill_up_b', kraam_type=kraam_type)
        fill_up_strategy_b_list.run()
        markt.kramen.remove_kraam_type(kraam_type=kraam_type)
        markt.report_indeling()

    trace.log('\n======> REMAINING STRATEGY')
    remaining_query = dict(kraam_type__not__in=[*KraamTypes], branche__not__in=verplichte_branches)
    remaining_strategy = HierarchyStrategy(markt, f'remaining_hierarchy', **remaining_query)
    remaining_strategy.run()
    fill_up_strategy_b_list = FillUpStrategyBList(markt, f'remaining_fill_up_b', **remaining_query)
    fill_up_strategy_b_list.run()

    trace.log(f"\n\n========FINAL ONDERNEMERS=======================\n")
    markt.report_ondernemers()

    stop = datetime.datetime.now()
    trace.log(f"{stop} - duration {stop - start}")

    output = {
        'toewijzingen': markt.get_allocation(),
        'afwijzingen': markt.get_rejections(),
    }
    return output


def parse_and_allocate(input_data):
    parsed = Parse(input_data)
    output = allocate(**parsed.__dict__)
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
