from collections import deque

class PERCLOSDetector:

    def __init__(self, window_size=150):
        self.window = deque(maxlen=window_size)

    def update(self, ear, threshold=0.25):

        if ear < threshold:
            self.window.append(1)
        else:
            self.window.append(0)

        if len(self.window) == 0:
            return 0

        perclos = sum(self.window) / len(self.window)

        return perclos