import cv2
import numpy as np


class FatigueGraph:

    def __init__(self, max_points=100):
        self.max_points = max_points
        self.values = []

    def update(self, score):

        self.values.append(score)

        if len(self.values) > self.max_points:
            self.values.pop(0)

    def draw(self):

        graph = np.zeros((200, 400, 3), dtype=np.uint8)

        if len(self.values) < 2:
            return graph

        step = 400 / self.max_points

        for i in range(1, len(self.values)):

            x1 = int((i-1) * step)
            y1 = 200 - int(self.values[i-1] * 2)

            x2 = int(i * step)
            y2 = 200 - int(self.values[i] * 2)

            cv2.line(graph, (x1, y1), (x2, y2), (0,255,0), 2)

        return graph