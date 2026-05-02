import cv2
import numpy as np
import time

class FatigueDashboard:

    def __init__(self):
        self.width = 500
        self.height = 350
        self.fatigue_score = 0
        self.history = []
        self.drowsy_count = 0
        self.last_state = "ALERT"
        self.last_update_time = time.time()

    def update(self, fatigue_score):
        self.fatigue_score = int(fatigue_score)

        # Store history (last 50 points)
        self.history.append(self.fatigue_score)
        if len(self.history) > 50:
            self.history.pop(0)

        # Count drowsiness events
        current_state = "ALERT"
        if fatigue_score > 70:
            current_state = "CRITICAL"
        elif fatigue_score > 40:
            current_state = "DROWSY"

        if current_state in ["DROWSY", "CRITICAL"] and self.last_state == "ALERT":
            self.drowsy_count += 1

        self.last_state = current_state
        self.last_update_time = time.time()

    def draw(self, score):

        dashboard = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # ---------------- TITLE ----------------
        cv2.putText(dashboard, "FATIGUE DASHBOARD",
                    (120, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255,255,255),
                    2)

        # ---------------- CONNECTION STATUS ----------------
        if time.time() - self.last_update_time < 2:
            status_text = "LIVE"
            status_color = (0,255,0)
        else:
            status_text = "DISCONNECTED"
            status_color = (0,0,255)

        cv2.putText(dashboard, f"Status: {status_text}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    status_color,
                    2)

        # ---------------- GAUGE ----------------
        center = (250, 200)
        radius = 100

        cv2.ellipse(dashboard, center, (radius, radius), 0, 180, 360, (200,200,200), 2)

        # Color logic
        if self.fatigue_score < 40:
            color = (0,255,0)
            label = "ALERT"
        elif self.fatigue_score < 70:
            color = (0,255,255)
            label = "DROWSY"
        else:
            color = (0,0,255)
            label = "CRITICAL"

        angle = int(180 + (self.fatigue_score / 100) * 180)

        needle_x = int(center[0] + radius * np.cos(np.radians(angle)))
        needle_y = int(center[1] + radius * np.sin(np.radians(angle)))

        cv2.line(dashboard, center, (needle_x, needle_y), color, 4)

        # ---------------- SCORE ----------------
        cv2.putText(dashboard,
                    f"{self.fatigue_score}",
                    (220, 180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (255,255,255),
                    3)

        # ---------------- LABEL ----------------
        cv2.putText(dashboard,
                    label,
                    (200, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2)

        # ---------------- DROWSY COUNT ----------------
        cv2.putText(dashboard,
                    f"Drowsy Events: {self.drowsy_count}",
                    (10, 300),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255,255,0),
                    2)

        # ---------------- MINI GRAPH ----------------
        if len(self.history) > 1:
            graph_x = 350
            graph_y = 250
            graph_w = 120
            graph_h = 80

            cv2.rectangle(dashboard,
                          (graph_x, graph_y - graph_h),
                          (graph_x + graph_w, graph_y),
                          (100,100,100),
                          1)

            for i in range(1, len(self.history)):
                x1 = graph_x + int((i-1)/50 * graph_w)
                y1 = graph_y - int((self.history[i-1]/100) * graph_h)

                x2 = graph_x + int(i/50 * graph_w)
                y2 = graph_y - int((self.history[i]/100) * graph_h)

                cv2.line(dashboard, (x1,y1), (x2,y2), (0,255,255), 2)

            cv2.putText(dashboard,
                        "Trend",
                        (graph_x, graph_y - graph_h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        (255,255,255),
                        1)

        return dashboard