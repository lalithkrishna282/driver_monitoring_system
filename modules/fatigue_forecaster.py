import numpy as np

class FatigueForecaster:

    def __init__(self):
        self.history = []

    def update(self, fatigue_score):
        self.history.append(fatigue_score)

        if len(self.history) > 50:
            self.history.pop(0)

    def predict(self):

        if len(self.history) < 5:
            return None

        x = np.arange(len(self.history))
        y = np.array(self.history)

        # Linear trend prediction
        slope, intercept = np.polyfit(x, y, 1)

        future_x = len(self.history) + 10
        prediction = slope * future_x + intercept

        prediction = int(max(0, min(100, prediction)))

        return prediction