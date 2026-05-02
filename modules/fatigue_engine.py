class FatigueEngine:

    def __init__(self, smoothing=0.35):
        self.score = 0
        self.smoothing = smoothing

    def compute_score(self, ear, perclos, blink_rate, mar, head_pitch, ear_threshold=0.23):

        score = 0.0
        eye_warning_threshold = ear_threshold + 0.04
        eye_span = max(0.06, eye_warning_threshold - max(0.10, ear_threshold - 0.04))

        # Eye closure severity. A softer curve avoids sudden jumps from one bad frame.
        if ear < eye_warning_threshold:
            score += min(30.0, max(0.0, (eye_warning_threshold - ear) / eye_span * 30.0))

        # Long eye closure trend (PERCLOS)
        if perclos > 0.20:
            score += min(35.0, max(0.0, (perclos - 0.20) / 0.45 * 35.0))

        # Ignore blink-rate scoring during startup while the estimate is unstable.
        if blink_rate > 0:
            if blink_rate < 8:
                score += min(12.0, (8 - blink_rate) / 8 * 12.0)
            elif blink_rate > 35:
                score += min(8.0, (blink_rate - 35) / 25 * 8.0)

        # Yawning detection
        if mar > 0.55:
            score += min(18.0, max(0.0, (mar - 0.55) / 0.35 * 18.0))

        # Head nodding
        if head_pitch > 20:
            score += min(20.0, (head_pitch - 20) / 25 * 20.0)

        raw_score = min(score, 100.0)
        self.score = (self.smoothing * raw_score) + ((1 - self.smoothing) * self.score)

        return round(self.score, 1)
