import logging
from colorlog import ColoredFormatter


class LogCollector:
    logs = []

    @classmethod
    def add(cls, log_level, message):
        cls.logs.append({"level": log_level, "message": message})


class LogProxy:
    def purge(self):
        LogCollector.logs = []

    def __init__(self, obj):
        self.obj = obj

    def debug(self, message):
        self.obj.debug(message)
        LogCollector.add("DEBUG", message)

    def info(self, message):
        self.obj.info(message)
        LogCollector.add("INFO", message)

    def warning(self, message):
        self.obj.warning(message)
        LogCollector.add("WARNING", message)

    def error(self, message):
        self.obj.error(message)
        LogCollector.add("ERROR", message)

    def critical(self, message):
        self.obj.critical(message)
        LogCollector.add("CRITICAL", message)

    def get_logs(self):
        return LogCollector.logs

    @property
    def disabled(self):
        return _clog.disabled

    @disabled.setter
    def disabled(self, is_disabled):
        _clog.disabled = is_disabled

    def set_level(self, level):
        _clog.setLevel(level)


LOG_LEVEL = logging.INFO
LOGFORMAT = (
    "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
)
PLAIN_LOGFORMAT = "  %(levelname)-8s | %(message)s"

formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setFormatter(formatter)
_clog = logging.getLogger("pythonConfig")
_clog.setLevel(LOG_LEVEL)
_clog.addHandler(stream)
clog = LogProxy(_clog)

formatter2 = logging.Formatter(PLAIN_LOGFORMAT)
stream2 = logging.StreamHandler()
stream2.setFormatter(formatter2)
_log = logging.getLogger("pythonConfig2")
_log.setLevel(LOG_LEVEL)
_log.addHandler(stream2)
log = LogProxy(_log)

# logging.disable(logging.CRITICAL)
# logging.disable(logging.NOTSET)

if __name__ == "__main__":
    clog.debug("A quirky message only developers care about")
    clog.info("Curious users might want to know this")
    clog.warning("Something is wrong and any user should be informed")
    clog.error("Serious stuff, this is red for a reason")
    clog.critical("OH NO everything is on fire")

    log.debug("Hooray say the roses")
    log.info("Today is blames day and we are red as blood")
