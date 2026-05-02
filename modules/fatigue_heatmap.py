import cv2
import numpy as np

class FatigueHeatmap:

    def __init__(self):
        self.size = 200

    def draw(self, fatigue_score):

        canvas = np.zeros((200,200,3), dtype=np.uint8)

        if fatigue_score < 40:
            color = (0,255,0)   # green
        elif fatigue_score < 70:
            color = (0,255,255) # yellow
        else:
            color = (0,0,255)   # red

        cv2.circle(canvas,(100,100),80,color,-1)

        cv2.putText(canvas,
                    f"{fatigue_score}",
                    (70,110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255,255,255),
                    2)

        cv2.putText(canvas,
                    "Fatigue",
                    (50,180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255,255,255),
                    2)

        return canvas