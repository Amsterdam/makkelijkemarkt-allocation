import logging
from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG
LOGFORMAT = (
    "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
)
PLAIN_LOGFORMAT = "  %(levelname)-8s | %(message)s"

formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setFormatter(formatter)
clog = logging.getLogger("pythonConfig")
clog.setLevel(LOG_LEVEL)
clog.addHandler(stream)

formatter2 = logging.Formatter(PLAIN_LOGFORMAT)
stream2 = logging.StreamHandler()
stream2.setFormatter(formatter2)
log = logging.getLogger("pythonConfig2")
log.setLevel(LOG_LEVEL)
log.addHandler(stream2)

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
