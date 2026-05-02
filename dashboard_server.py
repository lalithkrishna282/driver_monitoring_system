import csv
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parent
CSV_FILE = ROOT_DIR / "live_data.csv"
HOST = "127.0.0.1"
PORT = 8000
MAX_PORT_TRIES = 10


def _read_live_data():
    if not CSV_FILE.exists():
        return {"fatigue": 0.0, "attention": 0.0, "risk": 0.0, "source": "missing_csv"}

    try:
        with CSV_FILE.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return {"fatigue": 0.0, "attention": 0.0, "risk": 0.0, "source": "empty_csv"}

        row = rows[-1]
        return {
            "fatigue": float(row.get("fatigue", 0) or 0),
            "attention": float(row.get("attention", 0) or 0),
            "risk": float(row.get("risk", 0) or 0),
            "driver_name": row.get("driver_name", "Unknown") or "Unknown",
            "driver_number": int(float(row.get("driver_number", 0) or 0)),
            "source": "csv",
        }
    except Exception as exc:
        return {"fatigue": 0.0, "attention": 0.0, "risk": 0.0, "source": f"parse_error: {exc}"}


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/live-data":
            payload = _read_live_data()
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/":
            self.path = "/modules/dashboard.html"

        super().do_GET()


if __name__ == "__main__":
    server = None
    selected_port = None
    for port in range(PORT, PORT + MAX_PORT_TRIES):
        try:
            server = ThreadingHTTPServer((HOST, port), DashboardHandler)
            selected_port = port
            break
        except OSError:
            continue

    if server is None or selected_port is None:
        raise SystemExit(
            f"No free dashboard port found in range {PORT}-{PORT + MAX_PORT_TRIES - 1}"
        )

    print(f"Dashboard server running at http://{HOST}:{selected_port}")
    server.serve_forever()
