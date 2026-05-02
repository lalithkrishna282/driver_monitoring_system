import time

class BlinkDetector:

    def __init__(self, warmup_seconds=20):
        self.blink_count = 0
        self.start_time = time.time()
        self.warmup_seconds = warmup_seconds

    def add_blink(self):
        self.blink_count += 1

    def blink_rate(self):

        elapsed_seconds = time.time() - self.start_time

        if elapsed_seconds < self.warmup_seconds:
            return 0

        elapsed_minutes = elapsed_seconds / 60

        return self.blink_count / elapsed_minutes
