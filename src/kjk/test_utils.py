from pprint import pprint


class ErkenningsnummerNotFoudError(Exception):
    pass


class SollicitatienummerNotFoudError(Exception):
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


def alloc_sollnr(sollnr, data):
    """Get an allocation object by 'sollicitatieNummer'"""
    for toew in data["toewijzingen"]:
        if sollnr == toew["ondernemer"]["sollicitatieNummer"]:
            return toew
    raise SollicitatienummerNotFoudError(
        f"Sollicitatienummer {sollnr} not found in allocations"
    )


def stands_erk(erk, data):
    """Get allocated stands by 'erkenningsNummer'"""
    for toew in data["toewijzingen"]:
        if erk == toew["erkenningsNummer"]:
            return toew["plaatsen"]
    raise ErkenningsnummerNotFoudError(
        f"Erkenningsnummer {erk} not found in allocations"
    )


def reject_sollnr(sollnr, data):
    """Get a rejection object by 'sollicitatieNummer'"""
    for afw in data["afwijzingen"]:
        if sollnr == afw["ondernemer"]["sollicitatieNummer"]:
            return afw
    raise ErkenningsnummerNotFoudError(
        f"Sollicitatienummer {sollnr} not found in rejections"
    )


def reject_erk(erk, data):
    """Get a rejection object by 'erkenningsNummer'"""
    for afw in data["afwijzingen"]:
        if erk == afw["erkenningsNummer"]:
            return afw
    raise ErkenningsnummerNotFoudError(
        f"Erkenningsnummer {erk} not found in rejections"
    )
