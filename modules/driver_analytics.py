import cv2
import numpy as np

class DriverAnalytics:

    def __init__(self):
        self.fatigue_history = []
        self.yawn_history = []
        self.risk_history = []

    def update(self, fatigue, yawns, risk):

        self.fatigue_history.append(fatigue)
        self.yawn_history.append(yawns)
        self.risk_history.append(risk)

        if len(self.fatigue_history) > 100:
            self.fatigue_history.pop(0)
            self.risk_history.pop(0)

    def draw(self):

        canvas = np.zeros((300,400,3), dtype=np.uint8)

        if len(self.fatigue_history) == 0:
            return canvas

        avg_fatigue = int(np.mean(self.fatigue_history))
        max_fatigue = int(np.max(self.fatigue_history))
        total_yawns = max(self.yawn_history)

        risk_level = "LOW"

        if avg_fatigue > 60:
            risk_level = "HIGH"
        elif avg_fatigue > 35:
            risk_level = "MEDIUM"

        cv2.putText(canvas,"Driver Analytics",(80,30),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)

        cv2.putText(canvas,f"Avg Fatigue : {avg_fatigue}",(20,80),
                    cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)

        cv2.putText(canvas,f"Max Fatigue : {max_fatigue}",(20,120),
                    cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,255),2)

        cv2.putText(canvas,f"Yawns : {total_yawns}",(20,160),
                    cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,200,0),2)

        cv2.putText(canvas,f"Risk Level : {risk_level}",(20,200),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)

        return canvas