import numpy as np
import cv2


class FatigueGraph:

    def __init__(self):
        self.history = []

    def update(self, score):
        self.history.append(score)

        if len(self.history) > 100:
            self.history.pop(0)

    def draw(self):

        width = 500
        height = 200

        graph = np.zeros((height, width, 3), dtype=np.uint8)

        if len(self.history) < 2:
            return graph

        max_score = 100
        step = width / len(self.history)

        for i in range(1, len(self.history)):

            x1 = int((i - 1) * step)
            y1 = height - int((self.history[i - 1] / max_score) * height)

            x2 = int(i * step)
            y2 = height - int((self.history[i] / max_score) * height)

            cv2.line(graph, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return graph