import time

from modules.paths import FATIGUE_LOG_PATH


class FatigueLogger:

    def __init__(self, logfile=None):
        if logfile is None:
            logfile = FATIGUE_LOG_PATH
        self.logfile = logfile

    def log(self, fatigue_score):

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        line = f"{timestamp}, Fatigue Score: {fatigue_score}\n"

        with open(self.logfile, "a") as f:
            f.write(line)
