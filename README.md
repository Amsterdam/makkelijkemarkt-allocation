# makkelijkemarkt-allocations


# Dev setup

Maak een python 3+ venv:

    virtualenv venv

Activate:

    source venv/bin/activate

Install requirements:

    pip install -r requirements.txt


# Commands

Run de commands vanuit de `src` dir.

## run allocation

    python run_allocation.py

## run allocation unit tests

    python test_allocation.py

## run the all tests

    python tests.py

## run a single unittest

    python test_allocation.py BrancheScrutenizerTestCase.test_max_branches 

## run a single scenario test

    python tests.py TestBasicAllocation.test_assign_empty_stand

## run test with extra debug logging

    python tests.py DEBUG
    python tests.py TestBasicAllocation DEBUG
    python tests.py TestBasicAllocation.test_assign_empty_stand DEBUG


# Code formatting

Gebruik voor code formatting black. (https://github.com/psf/black)

    black .

en flake8 (https://flake8.pycqa.org/en/latest/)

    flake8 .

# Test coverage

Run een test suite met coverage: (https://coverage.readthedocs.io/en/6.2/)

    coverage run tests.py

Maak een coverage report:

    coverage report

    result:
    Name                                Stmts   Miss  Cover
    -------------------------------------------------------
    kjk/__init__.py                         0      0   100%
    kjk/allocation.py                     211     27    87%
    kjk/base.py                           438     56    87%
    kjk/inputdata.py                       82      3    96%
    kjk/outputdata.py                      74      6    92%
    kjk/utils.py                          168     18    89%
    test_allocation.py                    187      2    99%
    testcases/__init__.py                   0      0   100%
    testcases/alist_allocations.py         10      0   100%
    testcases/basic_allocations.py         95      0   100%
    testcases/branches_allocations.py      23      0   100%
    testcases/evi.py                       86      0   100%
    testcases/expansion.py                107      0   100%
    testcases/misc.py                      28      0   100%
    testcases/moving_vpl.py                20      0   100%
    testcases/soll.py                      18      0   100%
    testcases/vpl_allocations.py          110     12    89%
    tests.py                               13      0   100%
    -------------------------------------------------------
    TOTAL                                1670    124    93%


Uitgebreide html report

    coverage html
    
    result:
    "Wrote HTML report to htmlcov/index.html"

# generate diagram images

    docker run -u $UID -it -v /home/johan/Projects/amsterdam/origin/makkelijkemarkt-allocations/diagrams:/data minlag/mermaid-cli -i /data/overview.mmd -o /data/overview.png

# profiling

Dit runt de allocatie van de Dapper markt van 30-10-2021 met de standaard python profiler.
De profiler heeft wel overhead maar geeft inzicht in waar het performance knelpunt zit.

    python profile_allocation.py

# debugging

Het is mogelijk om de input van een allocatie vanuit de browser op te slaan en als input te gebruiken voor lokaal debuggen. Als Markten een bug rapporteert voor een markt, doorloop dan de volgende stappen:


1. Vraag om een markt en reproduceer de job met de issue: https://acc.kiesjekraam.amsterdam.nl/job/11/
2. Verander de job url in https://acc.kiesjekraam.amsterdam.nl/input/11/
3. Save de input data in een json file
4. In deze json zit een klein beetje protocol overhead in de form van een envelop. Dit heeft temaken met de bee-queue lib in KjK-TypeScript. Verwijder de envelop.

            {
              "data": {
               <allocation input is here>
              },
              "options": {
                "timestamp": 1653898452483,
                "stacktraces": []
              },
              "status": "created",
              "progress": 0
            }

5. Anonymiseer de data, run python script anonymizer `python anonymizer.py`
   (you will be prompted for the json path. Supply random integers as input for the other questions, i.e. 2 and 12)
6. Laad de opgeslagen fixture in de debug script. zie `debug.py`
7. Run de debug allocatie: `export $(cat ../.env.local) && python debug.py` (Zet de env vars voor de lokale redis)
8. De indeling is nu te bekijken op 127.0.0.1:8093/job/1


## overige debug tools

Om te achterhalen in welke allocatie fase een ondernemer of kraam is ingedeeld is een een debugger helper in `kjk.utils` (`from kjk.utils import AllocationDebugger`)

    dp = FixtureDataprovider("/home/johan/Desktop/eb-bak-zwaar_5.json")
    allocator = Allocator(dp)
    allocator.get_allocation()


    debug_data = allocator.get_debug_data()
    db = AllocationDebugger(allocator.get_debug_data())
    phase = db.get_allocation_phase_for_merchant("1990030703")
    print(phase)
    phase = db.get_allocation_phase_for_stand('14')
    print(phase)

    output:
    >>> merchant: 1990030703 -> Phase 2
    >>> stand: 14 -> Phase 2


## verbose logging

De meeste allocatie methods in de base allocatie class hebben een debug parameter om de slice van de ondernemers te loggen die op dat moment worden ingedeeld. Dit is de `print_df` paramater.

    self._allocate_vpl_for_query("status == 'vpl' & will_move == 'no'", print_df=True)

## testing util functions

In de module `kjk.test_utils` zijn enkele test utils opgenomen. Om bijvoorbeeld te testen of sollicitatienummer `63` plaats `75` heeft gekregen kun je de volgende code gebruiken. Zie de module voor meer info.

    tw = alloc_sollnr(63, self.market_allocation)
    self.assertListEqual(tw["plaatsen"], ["75"])