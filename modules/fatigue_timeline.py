import numpy as np
from collections import deque

class FatigueTimeline:

    def __init__(self, window=30):
        self.history = deque(maxlen=window)

    def update(self, fatigue_score):
        self.history.append(fatigue_score)

    def predict_future(self):

        if len(self.history) < 10:
            return None

        x = np.arange(len(self.history))
        y = np.array(self.history)

        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        future = y[-1] + slope * 10

        return int(max(0, min(100, future)))