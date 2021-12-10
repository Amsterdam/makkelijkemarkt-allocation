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
            except KeyError as e:
                pass
        if status_ok:
            clog.info("-> OK")
        else:
            clog.error("Failed: \n")
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
            except KeyError as e:
                pass
        if status_ok:
            clog.info("-> OK")
        else:
            clog.error("Failed: \n")
            print(tabulate(errors, headers="firstrow"))
            clog.info("")
