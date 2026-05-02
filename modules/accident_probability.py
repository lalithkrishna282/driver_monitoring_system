import numpy as np

class AccidentProbability:

    def __init__(self):
        self.history = []

    def compute(self, fatigue, attention, blink_rate, yawns):

        fatigue_factor = fatigue / 100
        attention_factor = (100 - attention) / 100
        blink_factor = min(blink_rate / 30, 1)
        yawn_factor = min(yawns / 5, 1)

        probability = (
            0.4 * fatigue_factor +
            0.3 * attention_factor +
            0.2 * blink_factor +
            0.1 * yawn_factor
        )

        probability = min(max(probability, 0), 1)

        percent = int(probability * 100)

        self.history.append(percent)

        if len(self.history) > 100:
            self.history.pop(0)

        return percent