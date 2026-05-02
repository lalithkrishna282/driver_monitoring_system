import numpy as np
from collections import deque


class DriverProfile:

    def __init__(self, window=120):

        self.ear_history = deque(maxlen=window)
        self.blink_history = deque(maxlen=window)
        self.fatigue_history = deque(maxlen=window)

    def update(self, ear, blink_rate, fatigue_score):

        self.ear_history.append(ear)
        self.blink_history.append(blink_rate)
        self.fatigue_history.append(fatigue_score)

    def baseline_ear(self):

        if len(self.ear_history) < 20:
            return None

        return float(np.percentile(self.ear_history, 75))

    def baseline_blink(self):

        if len(self.blink_history) < 20:
            return None

        return float(np.mean(self.blink_history))

    def fatigue_baseline(self):

        if len(self.fatigue_history) < 20:
            return None

        return float(np.mean(self.fatigue_history))
