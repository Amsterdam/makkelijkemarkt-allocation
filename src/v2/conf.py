from enum import Enum

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
