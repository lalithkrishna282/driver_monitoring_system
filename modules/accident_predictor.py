import numpy as np

class AccidentPredictor:

    def __init__(self, smoothing=0.30):
        self.history = []
        self.risk = 0
        self.smoothing = smoothing

    def compute_risk(self, fatigue, attention, blink_rate, yawns):

        fatigue_factor = fatigue * 0.4
        attention_factor = (100 - attention) * 0.3
        blink_factor = 0
        if blink_rate > 0:
            if blink_rate < 8:
                blink_factor = (8 - blink_rate) * 1.2
            elif blink_rate > 35:
                blink_factor = min(15, (blink_rate - 35) * 0.5)
        yawn_factor = min(20, yawns * 2)

        raw_risk = fatigue_factor + attention_factor + blink_factor + yawn_factor

        raw_risk = min(100, max(0, raw_risk))
        self.risk = (self.smoothing * raw_risk) + ((1 - self.smoothing) * self.risk)

        self.history.append(self.risk)

        return round(self.risk, 1)
