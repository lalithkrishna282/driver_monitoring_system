import numpy as np
import time


def compute_mar(mouth):
    """
    Compute Mouth Aspect Ratio (MAR)
    """

    A = np.linalg.norm(mouth[2] - mouth[10])
    B = np.linalg.norm(mouth[4] - mouth[8])
    C = np.linalg.norm(mouth[0] - mouth[6])

    mar = (A + B) / (2.0 * C)

    return mar


class YawnDetector:
    """
    Detect yawning based on MAR over consecutive frames
    """

    def __init__(self, mar_threshold=0.6, consec_frames=15):

        self.mar_threshold = mar_threshold
        self.consec_frames = consec_frames

        self.counter = 0
        self.yawn_count = 0
        self.last_yawn_time = time.time()

    def update(self, mar):

        yawn_detected = False

        if mar > self.mar_threshold:
            self.counter += 1
        else:

            if self.counter >= self.consec_frames:
                self.yawn_count += 1
                yawn_detected = True

            self.counter = 0

        return yawn_detected, self.yawn_count