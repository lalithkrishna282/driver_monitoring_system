import numpy as np

class AttentionDetector:

    def __init__(self, smoothing=0.35):
        self.attention_score = 100
        self.smoothing = smoothing

    def compute_attention(self, yaw, pitch):

        score = 100.0

        yaw_penalty = min(45.0, max(0.0, (abs(yaw) - 15) / 30 * 45.0))
        pitch_penalty = min(35.0, max(0.0, (pitch - 12) / 28 * 35.0))

        score -= yaw_penalty + pitch_penalty

        score = max(0.0, score)

        self.attention_score = (
            self.smoothing * score
            + (1 - self.smoothing) * self.attention_score
        )

        return round(self.attention_score, 1)

    def gaze_direction(self, yaw):

        if yaw > 20:
            return "RIGHT"

        elif yaw < -20:
            return "LEFT"

        else:
            return "CENTER"
