import csv
import os

class TrainingDataLogger:

    def __init__(self):
        self.file = "driver_training_data.csv"

        if not os.path.exists(self.file):
            with open(self.file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "EAR",
                    "PERCLOS",
                    "BLINK_RATE",
                    "MAR",
                    "PITCH",
                    "ATTENTION",
                    "FATIGUE_SCORE"
                ])

    def log(self, ear, perclos, blink_rate, mar, pitch, attention, fatigue):

        with open(self.file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ear,
                perclos,
                blink_rate,
                mar,
                pitch,
                attention,
                fatigue
            ])