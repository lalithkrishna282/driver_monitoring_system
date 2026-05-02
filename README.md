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

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If phone detection is enabled, make sure `ultralytics` and `torch` are installed. The app expects `yolov8n.pt` in the project root.

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

## Notes

- Runtime files such as logs, local database files, live CSV output, registered driver images, and virtual environments are intentionally ignored by Git.
- The facial landmark model is included under `models/` and is close to GitHub's large-file warning threshold.
