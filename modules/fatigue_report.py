from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime

from modules.paths import REPORTS_DIR


class FatigueReport:

    def __init__(self):
        self.scores = []
        self.yawns = 0

    def update(self, score, yawns):
        self.scores.append(score)
        self.yawns = yawns

    def generate(self):

        if len(self.scores) == 0:
            print("No data to generate report")
            return

        avg_score = sum(self.scores) / len(self.scores)
        max_score = max(self.scores)

        REPORTS_DIR.mkdir(exist_ok=True)
        filename = REPORTS_DIR / "driver_fatigue_report.pdf"

        c = canvas.Canvas(str(filename), pagesize=letter)

        c.setFont("Helvetica", 14)
        c.drawString(200, 750, "Driver Fatigue Report")

        c.setFont("Helvetica", 12)

        c.drawString(100, 700, f"Date: {datetime.datetime.now()}")
        c.drawString(100, 670, f"Average Fatigue Score: {avg_score:.2f}")
        c.drawString(100, 640, f"Maximum Fatigue Score: {max_score}")
        c.drawString(100, 610, f"Total Yawns: {self.yawns}")

        if max_score > 70:
            risk = "High Risk"
        elif max_score > 40:
            risk = "Moderate Risk"
        else:
            risk = "Low Risk"

        c.drawString(100, 580, f"Driver Risk Level: {risk}")

        c.save()

        print("Fatigue report generated:", filename)
