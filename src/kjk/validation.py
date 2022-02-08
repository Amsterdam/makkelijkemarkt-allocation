from kjk.logging import clog, log
from tabulate import tabulate


class ValidatorMixin:
    def validate_double_allocation(self):
        log.info("-" * 60)
        log.info("Valideren dubbel toegewezen kramen: ")
        tws = self.market_output.to_data()["toewijzingen"]
        stds = []
        doubles = []
        for tw in tws:
            for p in tw["plaatsen"]:
                if p not in stds:
                    stds.append(p)
                else:
                    doubles.append(p)
        if len(doubles) == 0:
            clog.info("-> OK")
        else:
            clog.error("Failed")

    def correct_expansion(self):
        return self.validate_expansion(verbose=False)

    def validate_expansion(self, verbose=True):
        merchants_to_be_rejected = []
        if verbose:
            log.info("-" * 60)
            log.info("Valideren uitbreidingen kramen: ")
        tws = self.market_output.to_data()["toewijzingen"]
        status_ok = True
        errors = [
            (
                "erkenningsNummer",
                "status",
                "message",
            )
        ]
        msgs = [
            (
                "erkenningsNummer",
                "status",
                "message",
            )
        ]
        for tw in tws:
            len_fixed = 0
            try:
                erk = tw["ondernemer"]["erkenningsNummer"]
                status = tw["ondernemer"]["status"]
                _max = tw["ondernemer"]["voorkeur"]["maximum"]
                _min = tw["ondernemer"]["voorkeur"]["minimum"]
                _num = len(tw["plaatsen"])
                if status in ("vpl", "tvpl", "exp", "expf"):
                    len_fixed = len(tw["ondernemer"]["plaatsen"])
                if status == "soll":
                    len_fixed = 1
                if len_fixed < _num:
                    msgs.append(
                        (erk, status, f" uitbreiding van {len_fixed} naar {_num}")
                    )
                if _num > _max:
                    status_ok = False
                    errors.append(
                        (erk, status, f"aantal kramen {_num} groter dan max {_max}")
                    )
                if not _min:
                    _min = 1.0
                # exp and expf can not have minimum
                if _min > _num and status not in ("exp", "expf"):
                    status_ok = False
                    errors.append(
                        (erk, status, f"aantal kramen {_num} kleiner dan min {_min}")
                    )
                    merchants_to_be_rejected.append(erk)
            except KeyError:
                pass
        if verbose:
            if status_ok:
                clog.info("-> OK")
                if not clog.disabled:
                    print(tabulate(msgs, headers="firstrow"))
            else:
                clog.error("Failed: \n")
                if not clog.disabled:
                    print(tabulate(errors, headers="firstrow"))
                clog.info("")
        return merchants_to_be_rejected

    def validate_branche_allocation(self):
        log.info("-" * 60)
        log.info("Valideren branche toegewezen kramen: ")
        tws = self.market_output.to_data()["toewijzingen"]
        status_ok = True
        errors = [
            (
                "erkenningsNummer",
                "plaatsId",
                "branche ondernemer",
                "branche kraam",
                "status",
            )
        ]
        for tw in tws:
            try:
                branches = tw["ondernemer"]["voorkeur"]["branches"]
                if len(branches) > 0:
                    required = self.cluster_finder.branche_is_required(branches[0])
                    for std in tw["plaatsen"]:
                        if required:
                            branche = self.cluster_finder.get_branche_for_stand_id(std)
                            if branches[0] not in branche:
                                status_ok = False
                                errors.append(
                                    (
                                        tw["ondernemer"]["erkenningsNummer"],
                                        std,
                                        branches[0],
                                        branche,
                                        tw["ondernemer"]["status"],
                                    )
                                )
            except KeyError:
                pass
        if status_ok:
            clog.info("-> OK")
        else:
            clog.error("Failed: \n")
            if not clog.disabled:
                print(tabulate(errors, headers="firstrow"))
            clog.info("")

    def validate_evi_allocations(self):
        log.info("-" * 60)
        log.info("Valideren evi toegewezen kramen: ")
        tws = self.market_output.to_data()["toewijzingen"]
        status_ok = True
        errors = [
            (
                "plaatsId",
                "erkenningsNummer",
                "vaste plaatsen",
                "toegewezen plaatsen",
                "status",
            )
        ]
        for tw in tws:
            try:
                evi = tw["ondernemer"]["voorkeur"]["verkoopinrichting"]
                if len(evi) > 0 and tw["ondernemer"]["status"] not in (
                    "vpl",
                    "vplz",
                    "exp",
                ):
                    for pl in tw["plaatsen"]:
                        if pl not in self.evi_ids:
                            status_ok = False
                            errors.append(
                                (
                                    pl,
                                    tw["ondernemer"]["erkenningsNummer"],
                                    tw["ondernemer"]["plaatsen"],
                                    tw["plaatsen"],
                                    tw["ondernemer"]["status"],
                                )
                            )
            except KeyError:
                pass
        if status_ok:
            clog.info("-> OK")
        else:
            clog.error("Failed: \n")
            print(tabulate(errors, headers="firstrow"))
            clog.info("")

    def correct_preferences(self):
        return self.validate_preferences(verbose=False)

    def validate_preferences(self, verbose=True):
        if verbose:
            log.info("-" * 60)
            log.info("Valideren plaatsvookeuren.")
        tws = self.market_output.to_data()["toewijzingen"]
        pref_dict = {}
        status_ok = True
        merchants_to_be_rejected = []
        errors = [
            (
                "erkenningsNummer",
                "voorkeur",
                "toegewezen plaatsen",
                "status",
                "flexibel",
            )
        ]
        for pref in self.prefs:
            erk = pref["erkenningsNummer"]
            pl = pref["plaatsId"]
            if erk not in pref_dict:
                pref_dict[erk] = []
            pref_dict[erk].append(pl)
        for tw in tws:
            erk = tw["erkenningsNummer"]
            status = tw["ondernemer"]["status"]
            try:
                flex = tw["ondernemer"]["voorkeur"]["anywhere"]
            except KeyError:
                flex = None
            for p in tw["plaatsen"]:
                try:
                    prefs = pref_dict[erk]
                    if p not in prefs and flex is False and status == "soll":
                        status_ok = False
                        _pref = (prefs[:8] + ["..."]) if len(prefs) > 8 else prefs
                        errors.append((erk, _pref, p, status, flex))
                        merchants_to_be_rejected.append(erk)
                except KeyError:
                    pass
        if verbose:
            if status_ok:
                clog.info("-> OK")
            else:
                clog.error("Failed: \n")
                print(tabulate(errors, headers="firstrow"))
                clog.info("")
        return merchants_to_be_rejected
