from v2.conf import TraceMixin


class ValidateMarkt(TraceMixin):
    def __init__(self, markt):
        self.markt = markt
        self.validate()

    def validate(self):
        self.trace.set_phase(epic='parse', story='validate')
        self.trace.set_event_phase()
        self.validate_ondernemers_own_kramen_are_right_branche()

    def validate_ondernemers_own_kramen_are_right_branche(self):
        self.trace.set_phase(task='kraam_and_owner_have_same_branche')
        for ondernemer in self.markt.ondernemers.all():
            for kraam_id in ondernemer.own:
                try:
                    kraam = self.markt.kramen.kramen_map[kraam_id]
                except KeyError:
                    self.trace.log(f"VALIDATION WARNING: kraam {kraam_id} not found in markt config")
                else:
                    if kraam.branche and kraam.branche.verplicht and kraam.branche != ondernemer.branche:
                        self.trace.log(f"VALIDATION WARNING: kraam {kraam} branche {kraam.branche} different branche as "
                                       f"owner {ondernemer}")
