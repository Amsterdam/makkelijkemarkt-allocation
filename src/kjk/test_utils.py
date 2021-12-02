class ErkenningsnummerNotFoudError(BaseException):
    pass


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
