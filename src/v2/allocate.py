import datetime
import json

from v2.markt import Markt
from v2.conf import logger, KraamTypes
from v2.strategy import ReceiveOwnKramenStrategy, HierarchyStrategy, FillUpStrategyBList
from v2.validate import ValidateMarkt
from v2.parse import Parse

# from v2.fixtures.kramen import rows as fix_rows
# from v2.fixtures.branches import branches as fix_branches
# from v2.fixtures.ondernemers import ondernemers as fix_ondernemers
# from v2.fixtures.markt import markt_meta as fix_markt_meta


def allocate(markt_meta, rows, branches, ondernemers, *args, **kwargs):
    start = datetime.datetime.now()
    logger.log(f"start {start}")

    markt = Markt(markt_meta, rows, branches, ondernemers)
    ValidateMarkt(markt)

    receive_own_kramen_strategy = ReceiveOwnKramenStrategy(markt)
    receive_own_kramen_strategy.run()

    verplichte_branches = markt.get_verplichte_branches()
    for branche in verplichte_branches:
        logger.log(f'\n======> VERPLICHTE BRANCHE {branche}')
        verplichte_branche_strategy = HierarchyStrategy(markt, f'verplichte_branche_hierarchy {branche}',
                                                        branche=branche)
        verplichte_branche_strategy.run()
        logger.log('\n==> FILL UP')
        fill_up_strategy_b_list = FillUpStrategyBList(markt, f'verplichte_branche_fill_up_b {branche}', branche=branche)
        fill_up_strategy_b_list.run()
        markt.kramen.remove_verplichte_branche(branche=branche)
        markt.report_indeling()

    for kraam_type in KraamTypes.BAK, KraamTypes.BAK_LICHT, KraamTypes.EVI:
        logger.log(f'\n======> Kraam type: {kraam_type}')
        bak_strategy = HierarchyStrategy(markt, f'{kraam_type} hierarchy', kraam_type=kraam_type)
        bak_strategy.run()
        fill_up_strategy_b_list = FillUpStrategyBList(markt, f'{kraam_type} fill_up_b', kraam_type=kraam_type)
        fill_up_strategy_b_list.run()
        markt.kramen.remove_kraam_type(kraam_type=kraam_type)
        markt.report_indeling()

    logger.log('\n======> REMAINING STRATEGY')
    remaining_query = dict(kraam_type__not__in=[*KraamTypes], branche__not__in=verplichte_branches)
    remaining_strategy = HierarchyStrategy(markt, f'remaining_hierarchy', **remaining_query)
    remaining_strategy.run()
    fill_up_strategy_b_list = FillUpStrategyBList(markt, f'remaining_fill_up_b', **remaining_query)
    fill_up_strategy_b_list.run()

    logger.log(f"\n\n========FINAL ONDERNEMERS=======================\n")
    markt.report_ondernemers()

    stop = datetime.datetime.now()
    logger.log(f"{stop} - duration {stop - start}")

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
    logs = logger.get_logs()
    return enriched_output, logs


if __name__ == '__main__':
    # to use json input from file use:
    # json_file = '/Users/pim/projects/notebook/allocation/v2/input_data/local.json'
    # parsed = Parse(json_file=json_file)

    # json_file = '/Users/pim/projects/notebook/allocation/v2/input_data/4045_2023-01-12.json'
    # json_file = '/Users/pim/projects/notebook/allocation/v2/input_data/AC-2023-01-21.json'
    json_file = '/Users/pim/projects/notebook/allocation/v2/input_data/ACC-AC-2023-01-18.json'
    logger.local = True
    parsed = Parse(json_file=json_file)
    output = allocate(**parsed.__dict__)

    logs = logger.get_logs()
    json.dumps(logs)

    # for fixtures use:
    # output = allocate(fix_markt_meta, fix_rows, fix_branches, fix_ondernemers)
