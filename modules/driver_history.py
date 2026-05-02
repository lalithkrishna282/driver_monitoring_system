import csv
import os
import datetime

from modules.paths import DRIVER_HISTORY_PATH

class DriverHistory:

    def __init__(self, file=None):

        self.file = file or DRIVER_HISTORY_PATH

        if not os.path.exists(self.file):

            with open(self.file, "w", newline="") as f:

                writer = csv.writer(f)

                writer.writerow([
                    "Driver",
                    "Date",
                    "Average Fatigue",
                    "Max Fatigue",
                    "Total Yawns",
                    "Risk Level"
                ])

    def log(self, driver, avg_score, max_score, yawns):

        if max_score > 70:
            risk = "High"
        elif max_score > 40:
            risk = "Medium"
        else:
            risk = "Low"

        with open(self.file, "a", newline="") as f:

            writer = csv.writer(f)

            writer.writerow([
                driver,
                datetime.datetime.now(),
                round(avg_score,2),
                max_score,
                yawns,
                risk
            ])

        print("Driver session stored in history")
