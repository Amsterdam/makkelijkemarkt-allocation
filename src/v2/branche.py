class Branche:
    def __init__(self, id=None, max=None, verplicht=False):
        self.id = id
        self.max = max
        self.verplicht = verplicht
        self.assigned_count = 0
        self.short_code = f"{'V' if self.verplicht else ''}{'M' if self.max else ''}"

    def __str__(self):
        return f"Branche {self.short_code}{self.id}" if self.id else 'Geen branche'

    @property
    def shortname(self):
        return f"{self.short_code}{str(self.id)[0:3]}" if self.id else 'geen'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, Branche):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return self.id
