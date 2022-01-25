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


# Code formatting

Gebruik voor code formatting black. (https://github.com/psf/black)

    black .


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


