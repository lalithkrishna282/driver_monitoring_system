import sqlite3
import time

class DriverDatabase:

    def __init__(self, db_path="driver_fatigue.db"):
        self.db_path = db_path

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
CREATE TABLE IF NOT EXISTS fatigue_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_name TEXT,
    fatigue_score INTEGER,
    state TEXT,
    ear REAL,
    blink_rate REAL,
    mar REAL,
    attention_score REAL,
    risk_score REAL,
    timestamp TEXT
)
""")
        self.conn.commit()

    def log(self, driver_name, fatigue_score, state,
        ear=None, blink_rate=None, mar=None,
        attention_score=None, risk_score=None):

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("""
INSERT INTO fatigue_log(
driver_name,
fatigue_score,
state,
ear,
blink_rate,
mar,
attention_score,
risk_score,
timestamp
)
VALUES(?,?,?,?,?,?,?,?,?)
""",
(
driver_name,
fatigue_score,
state,
ear,
blink_rate,
mar,
attention_score,
risk_score,
timestamp
))
        self.conn.commit()
