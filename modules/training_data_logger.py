import csv
import os

from modules.paths import TRAINING_DATA_PATH

class TrainingDataLogger:

    def __init__(self, file=None):
        self.file = file or TRAINING_DATA_PATH

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
