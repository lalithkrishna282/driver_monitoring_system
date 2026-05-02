import numpy as np
from collections import deque


class DriverRiskAI:

    def __init__(self, window_size=60):

        # store last N fatigue scores
        self.history = deque(maxlen=window_size)

    def update(self, fatigue_score):

        self.history.append(fatigue_score)

    def compute_risk(self):

        if len(self.history) < 10:
            return 0

        scores = np.array(self.history)

        avg = np.mean(scores)
        trend = scores[-1] - scores[0]

        risk = 0

        # base risk from fatigue
        risk += avg * 0.6

        # trend risk
        if trend > 10:
            risk += 20

        # spike detection
        if scores[-1] > 70:
            risk += 20

        risk = min(100, int(risk))

        return risk