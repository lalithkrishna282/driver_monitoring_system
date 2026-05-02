from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DRIVERS_DIR = BASE_DIR / "drivers"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
LIVE_DATA_PATH = BASE_DIR / "live_data.csv"
DRIVER_HISTORY_PATH = BASE_DIR / "driver_history.csv"
DRIVER_DB_PATH = BASE_DIR / "driver_fatigue.db"
FATIGUE_LOG_PATH = BASE_DIR / "fatigue_log.txt"
TRAINING_DATA_PATH = BASE_DIR / "driver_training_data.csv"


def ensure_runtime_dirs():
    DRIVERS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
