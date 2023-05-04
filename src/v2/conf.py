from enum import Enum
import json

BAK_TYPE_BRANCHE_IDS = ['bak', 'bak-licht']
EXP_BRANCHE = '401 -  Overig markt - Experimentele zone'


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
    UNKNOWN = 'n/a'

    def __hash__(self):
        return hash('Status')


ALL_VPH_STATUS = [Status.VPL, Status.TVPL, Status.TVPLZ, Status.EB, Status.EXP, Status.EXPF]
ALL_SOLL_STATUS = [Status.SOLL, Status.B_LIST]


class KraamTypes(ComparableEnum):
    BAK = 'B'
    BAK_LICHT = 'L'
    EVI = 'E'

    def __hash__(self):
        return hash('KraamType')


class RejectionReason(ComparableEnum):
    UNKNOWN = 0
    BRANCHE_FULL = 1
    ADJACENT_UNAVAILABLE = 2
    MINIMUM_UNAVAILABLE = 3
    MARKET_FULL = 4
    VPL_POSITION_NOT_AVAILABLE = 5
    PREF_NOT_AVAILABLE = 6
    PREF_NOT_AVAILABLE_ANYWHERE = 7
    KRAAM_DOES_NOT_EXIST = 8

    def __hash__(self):
        return hash('RejectionReason')


REJECTION_REASON_NL = {
    'UNKNOWN': 'Onbekend.',
    'BRANCHE_FULL': 'Alle marktplaatsen voor deze branche zijn reeds ingedeeld.',
    'ADJACENT_UNAVAILABLE': 'Geen aansluitende locatie gevonden met huidige voorkeuren.',
    'MINIMUM_UNAVAILABLE': 'Minimum aantal plaatsen niet beschikbaar.',
    'MARKET_FULL': 'Alle marktplaatsen zijn reeds ingedeeld.',
    'VPL_POSITION_NOT_AVAILABLE': 'De vaste plaatsen voor de vpl zijn niet beschikbaar.',
    'PREF_NOT_AVAILABLE': 'Geen geschikte locatie gevonden met huidige voorkeuren (en anywhere uit).',
    'PREF_NOT_AVAILABLE_ANYWHERE': 'Geen geschikte locatie gevonden met huidige voorkeuren (en anywhere aan).',
    'KRAAM_DOES_NOT_EXIST': 'Kraam bestaat niet.',
}


class Action(ComparableEnum):
    ASSIGN_KRAAM_TO_ONDERNEMER = 1
    UNASSIGN_KRAAM = 2


class Step:
    def __init__(self, id, action, kraam=None, ondernemer=None, detail='', phase='', group=''):
        self.id = id
        self.action = action.value
        self.kraam = kraam
        self.ondernemer = ondernemer
        self.detail = detail
        self.phase = phase
        self.group = group


class Trace:
    def __init__(self, rows=None):
        self.steps = []
        self.count = 1
        self.action = Action
        self.rows = rows or []
        self.task = ''
        self.story = ''
        self.epic = ''
        self.group = ''
        self.agent = ''
        self.cycle = 0

        self.log_detail_level = 1
        self.logs = []
        self.local = False

    @property
    def content(self):
        return {
            'steps': self.steps,
            'rows': self.rows,
        }

    def clear(self):
        self.logs = []

    def log(self, message, detail_level=1):
        phase = f"{self.epic}__{self.story}__{self.task}__{self.group}__{self.agent}"
        if self.cycle:
            phase += f":{self.cycle}"
        if detail_level >= self.log_detail_level:
            complete_message = f"{phase}: {message}"
            if self.local:
                print(complete_message)

            log_entry = {
                'level': detail_level,
                'message': complete_message,
            }
            self.logs.append(log_entry)

    def debug(self, message):
        task, group, agent = self.task, self.group, self.agent
        self.set_phase(task='debug', group=Status.UNKNOWN, agent=PhaseValue.event)
        self.log(message)
        self.set_phase(task=task, group=Status(group), agent=agent)

    def get_logs(self):
        return self.logs

    def set_rows(self, rows):
        self.rows = rows

    def set_phase(self, epic='', story='', task='', group=None, agent=''):
        if epic:
            self.epic = epic
        if story:
            self.story = story
        if task:
            self.task = task
        if group:
            self.group = group.value if group else ''
        if agent:
            self.agent = agent

    def set_cycle(self, cycle=0):
        self.cycle = cycle

    def set_report_phase(self, story='report', task='report'):
        self.set_phase(epic='report', story=story, task=task)
        self.set_event_phase()

    def set_event_phase(self):
        self.set_phase(group=Status.UNKNOWN, agent=PhaseValue.event)

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self.content, f)

    def add_step(self, **kwargs):
        phase = f"{self.epic}__{self.story}__{self.task}"
        self.steps.append(Step(id=self.count, phase=phase, group=self.group, **kwargs).__dict__)
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


class PhaseValue:
    unknown = Status.UNKNOWN
    event = 'event'


class HaltOptimizationException(Exception):
    pass
