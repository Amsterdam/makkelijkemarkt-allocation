from pprint import pprint


class ErkenningsnummerNotFoudError(BaseException):
    pass


def print_alloc(data):
    print("=" * 70)
    print("Allocation:")
    print("-" * 70)
    print("Toewijzingen:")
    pprint(data["toewijzingen"])
    print("-" * 70)
    print("Afwijzingen:")
    pprint(data["afwijzingen"])


def alloc_erk(erk, data):
    """Get an allocation object by 'erkenningsNummer'"""
    for toew in data["toewijzingen"]:
        if erk == toew["erkenningsNummer"]:
            return toew
    raise ErkenningsnummerNotFoudError(
        f"Erkenningsnummer {erk} not found in allocations"
    )


def stands_erk(erk, data):
    """Get allocated stands by 'erkenningsNummer'"""
    for toew in data["toewijzingen"]:
        if erk == toew["erkenningsNummer"]:
            return toew["plaatsen"]
    raise ErkenningsnummerNotFoudError(
        f"Erkenningsnummer {erk} not found in allocations"
    )


def reject_erk(erk, data):
    """Get a rejection object by 'erkenningsNummer'"""
    for afw in data["afwijzingen"]:
        if erk == afw["erkenningsNummer"]:
            return afw
    raise ErkenningsnummerNotFoudError(
        f"Erkenningsnummer {erk} not found in rejections"
    )
