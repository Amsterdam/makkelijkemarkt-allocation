from kjk.logging import clog, log


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
        log.info("-" * 60)

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
            log.info(tabulate(errors, headers="firstrow"))
        log.info("-" * 60)
