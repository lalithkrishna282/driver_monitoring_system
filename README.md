# Driver Monitoring System

Real-time driver drowsiness and fatigue monitoring using webcam input, facial landmarks, blink/yawn detection, phone detection, fatigue scoring, and a browser dashboard.

## Features

- Eye aspect ratio, blink, yawn, PERCLOS, and head-pose based fatigue signals
- Phone detection using YOLOv8
- Driver profile and history logging
- Local dashboard with live fatigue, attention, and risk metrics
- SQLite-backed fatigue history for local analytics

## Project Structure

```text
.
├── main.py
├── dashboard_server.py
├── modules/
├── dashboard/
├── models/
│   └── shape_predictor_68_face_landmarks.dat
├── yolov8n.pt
└── requirements.txt
```

## Setup

Use Python 3.10 or newer. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If phone detection is enabled, make sure `ultralytics` and `torch` are installed. The app expects `yolov8n.pt` in the project root.

## Smoke Check

Run the smoke check before a demo, submission, or deployment test:

```bash
python scripts/smoke_check.py
```

This verifies that required model files exist, creates runtime folders such as `drivers/`, `logs/`, and `reports/`, and checks that the Python source compiles. It does not start the webcam.

## Run

Start the main driver monitoring application:

```bash
python main.py
```

Start the standalone dashboard server:

```bash
python dashboard_server.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Runtime Files

The application creates local runtime files while it runs:

- `live_data.csv` for dashboard updates
- `driver_fatigue.db` for fatigue history
- `fatigue_log.txt` for fatigue score logs
- `drivers/` for locally registered driver images
- `reports/` for generated fatigue reports

These files are intentionally ignored by Git because they are machine-specific output, not source code.

## Troubleshooting

- If camera access fails, confirm your operating system has granted camera permission to the terminal or IDE.
- If `dlib` or `face_recognition` fails to install, install system build tools first. On macOS, installing Xcode command line tools usually helps.
- If the dashboard shows no data, run `python main.py` first so `live_data.csv` can be generated.
- If phone detection fails, confirm `yolov8n.pt` exists in the project root.

## Notes

- Runtime files such as logs, local database files, live CSV output, registered driver images, and virtual environments are intentionally ignored by Git.
- The facial landmark model is included under `models/` and is close to GitHub's large-file warning threshold.
