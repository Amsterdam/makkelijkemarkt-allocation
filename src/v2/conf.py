from enum import Enum
import json

BAK_TYPE_BRANCHE_IDS = ['bak', 'bak-licht']


class ComparableEnum(Enum):
    def __eq__(self, other):
        return self.value == getattr(other, 'value', None)


class Status(ComparableEnum):
    VPL = 'vpl'
    TVPL = 'tvpl'
    TVPLZ = 'tvplz'
    EB = 'eb'
    EXP = 'exp'
    EXPF = 'expf'
    SOLL = 'soll'
    B_LIST = 'b_list'
    UNKNOWN = 'unknown'

    def __hash__(self):
        return hash('Status')


ALL_VPH_STATUS = [Status.VPL, Status.TVPL, Status.TVPLZ, Status.EB]
ALL_SOLL_STATUS = [Status.SOLL, Status.B_LIST]


class KraamTypes(ComparableEnum):
    BAK = 'B'
    BAK_LICHT = 'L'
    EVI = 'E'

    def __hash__(self):
        return hash('KraamType')


class RejectionReason(ComparableEnum):
    LESS_THAN_MIN = 'Less kramen than minimum'
    NO_KRAMEN = 'No kramen proposed (but anywhere flag off)'
    NO_KRAMEN_WITH_ANYWHERE = 'No kramen proposed even with anywhere flag on'
    EXCEEDS_BRANCHE_MAX = 'Exceeds branche max'

    def __hash__(self):
        return hash('RejectionReason')


class Action(ComparableEnum):
    ASSIGN_KRAAM_TO_ONDERNEMER = 1
    UNASSIGN_KRAAM = 2


class Logger:
    def __init__(self):
        self.log_detail_level = 1
        self.logs = []
        self.local = False

    def log(self, message, detail_level=1):
        if detail_level >= self.log_detail_level:
            if self.local:
                print(f"{message}")

            log_entry = {
                'level': detail_level,
                'message': message,
            }
            self.logs.append(log_entry)

    def get_logs(self):
        return self.logs


logger = Logger()


class Step:
    def __init__(self, id, action, kraam=None, ondernemer=None, detail=''):
        self.id = id
        self.action = action.value
        self.kraam = kraam
        self.ondernemer = ondernemer
        self.detail = detail


class Trace:
    def __init__(self, rows=None):
        self.steps = []
        self.count = 1
        self.action = Action
        self.rows = rows or []

    @property
    def content(self):
        return {
            'steps': self.steps,
            'rows': self.rows,
        }

    def set_rows(self, rows):
        self.rows = rows

    def show(self):
        print(self.content)

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self.content, f)

    def add_step(self, **kwargs):
        self.steps.append(Step(id=self.count, **kwargs).__dict__)
        self.count += 1

    def assign_kraam_to_ondernemer(self, kraam, ondernemer):
        self.add_step(action=self.action.ASSIGN_KRAAM_TO_ONDERNEMER, kraam=kraam, ondernemer=ondernemer)

    def unassign_kraam(self, kraam):
        self.add_step(action=self.action.UNASSIGN_KRAAM, kraam=kraam)

    def assign_ondernemer_to_kraam(self):
        pass

    def unassign_ondernemer(self):
        pass

    def reject_ondernemer(self):
        pass


trace = Trace()


class TraceMixin:
    trace = trace
