import time


class FatigueLogger:

    def __init__(self, logfile="fatigue_log.txt"):
        self.logfile = logfile

    def log(self, fatigue_score):

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        line = f"{timestamp}, Fatigue Score: {fatigue_score}\n"

        with open(self.logfile, "a") as f:
            f.write(line)