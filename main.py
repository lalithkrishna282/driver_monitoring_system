import cv2
import dlib
import numpy as np
import os
import sys
import time
import torch
import subprocess
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
import pandas as pd
from pathlib import Path
import json
import threading
import sqlite3
import csv
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# ---------------- PERFORMANCE SETTINGS ----------------
frame_skip = 4
frame_count = 0
PHONE_DETECT_EVERY_N_FRAMES = 48
RECOGNIZE_DRIVER_EVERY_N_FRAMES = 90
GRADCAM_EVERY_N_FRAMES = 300
DB_LOG_INTERVAL = 1.0
TXT_LOG_INTERVAL = 2.0
DISPLAY_REFRESH_INTERVAL = 0.2
FACE_DETECT_SCALE = 0.5
RECOGNITION_SCALE = 0.25
ALERT_INTERVAL_SECONDS = 6
SHOW_DEBUG_WINDOWS = os.environ.get("SHOW_DEBUG_WINDOWS", "0") == "1"

last_dashboard_update = time.time()
dashboard_interval = 2  # seconds

last_csv_write = time.time()
csv_interval = 2  # seconds
last_db_log_time = time.time()
last_txt_log_time = time.time()
BASE_DIR = Path(__file__).resolve().parent

latest_live_data = {
    "fatigue": 0.0,
    "attention": 0.0,
    "risk": 0.0,
    "driver_name": "Unknown",
    "driver_number": 0,
}
live_data_lock = threading.Lock()
last_display_refresh = time.time()
last_rendered_frame = None
latest_heatmap = None
latest_dashboard = None
latest_live_graph = None
latest_analytics = None
csv_fields = ["fatigue", "attention", "risk", "driver_name", "driver_number"]


def _build_driver_number_map():
    names = []
    if DRIVERS_DIR.exists():
        for p in DRIVERS_DIR.iterdir():
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                names.append(p.stem)
    names = sorted(set(names))
    return {name: idx + 1 for idx, name in enumerate(names)}


def _write_live_data_csv(data):
    with LIVE_DATA_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerow(data)


def _speak_async(message):
    def _runner():
        try:
            if sys.platform == "darwin":
                subprocess.Popen(
                    ["say", message],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            if voice_engine is not None:
                voice_engine.say(message)
                voice_engine.runAndWait()
                return
        except Exception:
            pass

    threading.Thread(target=_runner, daemon=True).start()


def _driver_name_from_number(driver_number):
    mapping = _build_driver_number_map()
    for name, number in mapping.items():
        if number == driver_number:
            return name
    return None


def _driver_details_by_number(driver_number):
    if driver_number <= 0:
        return {"ok": False, "error": "driver number must be >= 1"}

    driver_name = _driver_name_from_number(driver_number)
    if not driver_name:
        return {"ok": False, "error": f"driver {driver_number} not found"}

    if not DRIVER_DB_PATH.exists():
        return {
            "ok": True,
            "driver_number": driver_number,
            "driver_name": driver_name,
            "samples": 0,
        }

    try:
        conn = sqlite3.connect(str(DRIVER_DB_PATH))
        cur = conn.cursor()
        cur.execute(
            """
            SELECT fatigue_score, state, attention_score, risk_score, timestamp
            FROM fatigue_log
            WHERE driver_name = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (driver_name,),
        )
        latest = cur.fetchone()

        cur.execute(
            """
            SELECT COUNT(*), AVG(fatigue_score), MAX(fatigue_score)
            FROM fatigue_log
            WHERE driver_name = ?
            """,
            (driver_name,),
        )
        stats = cur.fetchone()
        conn.close()

        samples = int(stats[0] or 0)
        payload = {
            "ok": True,
            "driver_number": driver_number,
            "driver_name": driver_name,
            "samples": samples,
            "avg_fatigue": round(float(stats[1]), 1) if stats[1] is not None else 0.0,
            "max_fatigue": float(stats[2]) if stats[2] is not None else 0.0,
        }
        if latest:
            payload.update(
                {
                    "latest_fatigue": float(latest[0]),
                    "latest_state": str(latest[1]),
                    "latest_attention": float(latest[2]) if latest[2] is not None else 0.0,
                    "latest_risk": float(latest[3]) if latest[3] is not None else 0.0,
                    "last_seen": str(latest[4]),
                }
            )
        return payload
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

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
            with live_data_lock:
                payload = dict(latest_live_data)
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

        if parsed.path == "/api/driver-details":
            qs = parse_qs(parsed.query)
            raw_driver = qs.get("driver", ["0"])[0]
            try:
                driver_number = int(raw_driver)
            except ValueError:
                driver_number = 0

            payload = _driver_details_by_number(driver_number)
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


def start_dashboard_server(host="127.0.0.1", port=8000, max_tries=10):
    server = None
    selected_port = None

    for candidate_port in range(port, port + max_tries):
        try:
            server = ThreadingHTTPServer((host, candidate_port), DashboardHandler)
            selected_port = candidate_port
            break
        except OSError:
            continue

    if server is None or selected_port is None:
        print(
            f"Dashboard server not started: no free port in range {port}-{port + max_tries - 1}"
        )
        return None

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    dashboard_url = f"http://{host}:{selected_port}"
    print(f"Dashboard available at {dashboard_url}")
    return dashboard_url
  
from modules.accident_probability import AccidentProbability
from imutils import face_utils
cv2.startWindowThread()
from modules.head_pose import get_head_pose
from modules.ear_detector import compute_ear
from modules.perclos_detector import PERCLOSDetector
from modules.blink_detector import BlinkDetector
from modules.yawn_detector import compute_mar, YawnDetector
from modules.cnn_eye_model import EyeCNN
from modules.gradcam import GradCAM
from modules.fatigue_engine import FatigueEngine
from modules.fatigue_logger import FatigueLogger
from modules.fatigue_graph import FatigueGraph
from modules.fatigue_live_graph import FatigueLiveGraph
from modules.fatigue_dashboard import FatigueDashboard
from modules.fatigue_timeline import FatigueTimeline
from modules.fatigue_report import FatigueReport
from modules.fatigue_predictor import FatiguePredictor
from modules.attention_detector import AttentionDetector
from modules.accident_predictor import AccidentPredictor
from modules.driver_risk_ai import DriverRiskAI
from modules.driver_profile import DriverProfile
from modules.phone_detector import PhoneDetector
from modules.driver_registration import DriverRegistration
from modules.driver_recognition import DriverRecognition
from modules.fatigue_heatmap import FatigueHeatmap
from modules.driver_database import DriverDatabase
from modules.driver_history import DriverHistory
from modules.driver_analytics import DriverAnalytics
from modules.fatigue_forecaster import FatigueForecaster
from modules.focus_zone import FocusZone
from modules.paths import (
    DRIVER_DB_PATH,
    DRIVERS_DIR,
    FATIGUE_LOG_PATH,
    LIVE_DATA_PATH,
    ensure_runtime_dirs,
)
# ---------------- Initialize Detectors ----------------

ensure_runtime_dirs()

perclos_detector = PERCLOSDetector()
blink_detector = BlinkDetector()
yawn_detector = YawnDetector()
# ---------------- Voice Alert System ----------------
try:
    voice_engine = pyttsx3.init() if pyttsx3 is not None and sys.platform != "darwin" else None
except Exception:
    voice_engine = None

if voice_engine is not None:
    voice_engine.setProperty('rate', 160)

last_voice_time = 0
voice_interval = ALERT_INTERVAL_SECONDS
current_time = time.time()
fatigue_engine = FatigueEngine()

fatigue_logger = FatigueLogger(str(FATIGUE_LOG_PATH))
fatigue_graph = FatigueGraph()
fatigue_live_graph = FatigueLiveGraph()
fatigue_dashboard = FatigueDashboard()
#fatigue_dashboard.update(fatigue_score)
#dashboard = fatigue_dashboard.draw(fatigue_score)
#cv2.imshow("Fatigue Dashboard", dashboard)
fatigue_heatmap = FatigueHeatmap()
fatigue_predictor = FatiguePredictor()
attention_detector = AttentionDetector()
driver_risk_ai = DriverRiskAI()
accident_predictor = AccidentPredictor()
driver_profile = DriverProfile()
phone_detector = PhoneDetector()
fatigue_timeline = FatigueTimeline()
fatigue_report = FatigueReport()
driver_registration = DriverRegistration(str(DRIVERS_DIR))
driver_recognition = DriverRecognition(str(DRIVERS_DIR))
driver_number_map = _build_driver_number_map()
driver_database = DriverDatabase(str(DRIVER_DB_PATH))
driver_history = DriverHistory()
driver_analytics = DriverAnalytics()
accident_probability = AccidentProbability()
fatigue_forecaster = FatigueForecaster()
focus_zone_detector = FocusZone()

EAR_THRESHOLD = 0.25
MIN_EAR_THRESHOLD = 0.18
MAX_EAR_THRESHOLD = 0.28
EAR_CALIBRATION_FRAMES = 45
EAR_CONSEC_FRAMES = 20

counter = 0
last_announcement = 0
announcement_interval = ALERT_INTERVAL_SECONDS

fatigue_score = 0
ear_calibration_samples = []
pitch_calibration_samples = []
yaw_calibration_samples = []
dynamic_ear_threshold = EAR_THRESHOLD
calibration_complete = False
neutral_pitch = 0.0
neutral_yaw = 0.0

# ---------------- Load Models ----------------

detector = dlib.get_frontal_face_detector()

predictor = dlib.shape_predictor(
    str(BASE_DIR / "models" / "shape_predictor_68_face_landmarks.dat")
)

model = EyeCNN()
model.eval()

gradcam = GradCAM(model)

# ---------------- Landmark Indexes ----------------

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

# ---------------- Camera ----------------
fatigue_graph.update(fatigue_score)
fatigue_live_graph.update(fatigue_score)
fatigue_graph.draw()

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
try:
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
except Exception:
    pass
# Default values (prevents NameError if no face detected)
# Default values to prevent NameError
ear = 0.0
perclos = 0.0
blink_rate = 0.0
mar = 0.0
pitch = 0.0
yaw = 0.0
fatigue_score = 0
attention_score = 0
gaze_dir = "CENTER"
head_state = "NO FACE IS THERE"
state = "NO FACE IS THERE"
total_yawns = 0
predicted_score = None
risk_score = 0
accident_prob = 0
future_fatigue = None
forecast_score = None
frame_count = 0
faces = []
driver_name = "Unknown"
driver_number = 0
phone_detected = False
phone_boxes = []
# ---------------- Driver Session Tracking ----------------
session_scores = []
max_session_score = 0
dashboard_url = start_dashboard_server()

if not cap.isOpened():
    print("Error: Camera not accessible")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # Skip frames for performance
    if frame_count % frame_skip != 0:
        continue
    # ----- Default values (prevents NameError when no face detected) -----
    ear = 0.0
    perclos = 0
    blink_rate = 0
    mar = 0
    pitch = 0
    yaw = 0
    fatigue_score = 0
    attention_score = 100
    risk_score = 0
    accident_prob = 0
    gaze_dir = "CENTER"
    head_state = "NO FACE IS THERE"
    state = "NO FACE IS THERE"
   
    name = "Unknown"

    display_now = time.time()

    # Phone detection (heavily throttled for smoother video loop)
    if frame_count % PHONE_DETECT_EVERY_N_FRAMES == 0:
        small_phone_frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
        detected, boxes = phone_detector.detect(small_phone_frame)
        phone_detected = detected
        phone_boxes = [(x1 * 2, y1 * 2, x2 * 2, y2 * 2) for (x1, y1, x2, y2) in boxes]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    small_gray = cv2.resize(gray, None, fx=FACE_DETECT_SCALE, fy=FACE_DETECT_SCALE)
    detected_faces = detector(small_gray)
    faces = [
        dlib.rectangle(
            int(face.left() / FACE_DETECT_SCALE),
            int(face.top() / FACE_DETECT_SCALE),
            int(face.right() / FACE_DETECT_SCALE),
            int(face.bottom() / FACE_DETECT_SCALE),
        )
        for face in detected_faces
    ]

    fatigue_graph.update(fatigue_score)
    fatigue_live_graph.update(fatigue_score)

    if len(faces) == 0:
     state = "NO FACE IS THERE"
     driver_name = "Unknown"
     driver_number = 0
    else:
     state = "FACE DETECTED"

    if len(faces) > 0 and frame_count % RECOGNIZE_DRIVER_EVERY_N_FRAMES == 0:
        recognition_frame = cv2.resize(frame, None, fx=RECOGNITION_SCALE, fy=RECOGNITION_SCALE)
        driver_name = driver_recognition.recognize(recognition_frame)
        if driver_name == "Unknown":
            driver_number = 0
        else:
            driver_number = driver_number_map.get(driver_name, 0)
    
    for face in faces:

        shape = predictor(gray, face)
        shape = face_utils.shape_to_np(shape)
                 # ---------------- GradCAM ----------------
        x, y, w, h = face_utils.rect_to_bb(face)
        frame_h, frame_w = gray.shape[:2]

        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(frame_w, x + w)
        y2 = min(frame_h, y + h)

        roi_w = x2 - x1
        roi_h = y2 - y1

        if roi_w <= 0 or roi_h <= 0:
            continue

        face_img = gray[y1:y2, x1:x2]

        if face_img.size > 0:

            eye_img = cv2.resize(face_img, (48, 48))
            eye_img = eye_img / 255.0

            eye_tensor = torch.from_numpy(eye_img).float().unsqueeze(0).unsqueeze(0)
            eye_tensor.requires_grad_()

            if frame_count % GRADCAM_EVERY_N_FRAMES == 0:
             heatmap = gradcam.generate(eye_tensor)
            else:
             heatmap = np.zeros((48,48), dtype=np.float32)

            heatmap = cv2.resize(heatmap, (roi_w, roi_h))
            heatmap = np.uint8(255 * heatmap)
            heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

            overlay = cv2.addWeighted(frame[y1:y2, x1:x2], 0.6, heatmap, 0.4, 0)
            frame[y1:y2, x1:x2] = overlay
        # ---------------- Eye Processing ----------------

        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]

        leftEAR = compute_ear(leftEye)
        rightEAR = compute_ear(rightEye)

        ear = (leftEAR + rightEAR) / 2.0
        if ear > 0:
            if not calibration_complete:
                ear_calibration_samples.append(ear)
                if len(ear_calibration_samples) >= EAR_CALIBRATION_FRAMES:
                    open_eye_ear = float(np.percentile(ear_calibration_samples, 75))
                    dynamic_ear_threshold = float(
                        np.clip(open_eye_ear * 0.72, MIN_EAR_THRESHOLD, MAX_EAR_THRESHOLD)
                    )
                    if pitch_calibration_samples:
                        neutral_pitch = float(np.median(pitch_calibration_samples))
                    if yaw_calibration_samples:
                        neutral_yaw = float(np.median(yaw_calibration_samples))
                    fatigue_engine.score = 0
                    attention_detector.attention_score = 100
                    accident_predictor.risk = 0
                    calibration_complete = True
                    print(
                        "Calibration complete: "
                        f"ear_baseline={open_eye_ear:.3f}, "
                        f"ear_threshold={dynamic_ear_threshold:.3f}, "
                        f"neutral_pitch={neutral_pitch:.1f}, "
                        f"neutral_yaw={neutral_yaw:.1f}"
                    )
            else:
                baseline_ear = driver_profile.baseline_ear()
                if baseline_ear is not None:
                    target_threshold = float(
                        np.clip(baseline_ear * 0.72, MIN_EAR_THRESHOLD, MAX_EAR_THRESHOLD)
                    )
                    dynamic_ear_threshold = (
                        0.98 * dynamic_ear_threshold + 0.02 * target_threshold
                    )

        perclos = perclos_detector.update(ear, threshold=dynamic_ear_threshold)

        if ear < dynamic_ear_threshold:
            counter += 1
        else:
            if counter >= EAR_CONSEC_FRAMES:
                blink_detector.add_blink()
            counter = 0

        blink_rate = blink_detector.blink_rate()
        # ---------------- Yawn Detection ----------------

        mouth = shape[mStart:mEnd]
        mar = compute_mar(mouth)

        yawn_detected, total_yawns = yawn_detector.update(mar)

        current_time = time.time()

        if (
            yawn_detected
            and current_time - last_voice_time > voice_interval
        ):
         _speak_async("Driver yawning detected. Please stay alert.")
         last_voice_time = current_time

        # ---------------- Head Pose ----------------

        pitch, yaw, roll = get_head_pose(shape, frame)
        raw_pitch = pitch
        raw_yaw = yaw

        if not calibration_complete:
            pitch_calibration_samples.append(raw_pitch)
            yaw_calibration_samples.append(raw_yaw)
        else:
            pitch = raw_pitch - neutral_pitch
            yaw = raw_yaw - neutral_yaw

        focus_zone = focus_zone_detector.detect(yaw, pitch)

        attention_score = attention_detector.compute_attention(yaw, pitch)
        gaze_dir = attention_detector.gaze_direction(yaw)

        if pitch > 20:
            head_state = "HEAD DOWN"
        elif abs(yaw) > 25:
            head_state = "LOOKING SIDE"
        else:
            head_state = "NORMAL"

        # ---------------- Fatigue Score ----------------

        fatigue_score = fatigue_engine.compute_score(
           
            ear,
            perclos,
            blink_rate,
            mar,
            pitch,
            dynamic_ear_threshold
        )
        current_time = time.time()
        fatigue_forecaster.update(fatigue_score)
        forecast_score = fatigue_forecaster.predict()
        risk_score = accident_predictor.compute_risk(
            fatigue_score,
            attention_score,
            blink_rate,
            total_yawns,
        )
        driver_analytics.update(
            fatigue_score,
            total_yawns,
            risk_score,
        )
        accident_prob = accident_probability.compute(
            fatigue_score,
            attention_score,
            blink_rate,
            total_yawns,
        )

    if len(faces) > 0 and not calibration_complete:
        fatigue_score = min(fatigue_score, 30)
        risk_score = min(risk_score, 15)

    # Store fatigue history
    session_scores.append(fatigue_score)
    if fatigue_score > max_session_score:
        max_session_score = fatigue_score

    current_time = time.time()
    data = {
        "fatigue": float(fatigue_score),
        "attention": float(attention_score),
        "risk": float(risk_score),
        "driver_name": str(driver_name),
        "driver_number": int(driver_number),
    }
    with live_data_lock:
        latest_live_data.update(data)

    if current_time - last_csv_write > csv_interval:
        _write_live_data_csv(data)
        print("CSV UPDATED:", data)
        last_csv_write = current_time
        latest_heatmap = fatigue_heatmap.draw(fatigue_score)

    fatigue_dashboard.update(fatigue_score)
    if current_time - last_dashboard_update > dashboard_interval:
        latest_dashboard = fatigue_dashboard.draw(fatigue_score)
        latest_live_graph = fatigue_live_graph.draw()
        latest_analytics = driver_analytics.draw()

        last_dashboard_update = current_time

    if current_time - last_txt_log_time > TXT_LOG_INTERVAL:
        fatigue_logger.log(fatigue_score)
        last_txt_log_time = current_time
    fatigue_timeline.update(fatigue_score)
    future_fatigue = fatigue_timeline.predict_future()
    fatigue_report.update(fatigue_score, total_yawns)

    driver_profile.update(ear, blink_rate, fatigue_score)
    fatigue_predictor.update(fatigue_score)
    predicted_score = fatigue_predictor.predict()
    driver_risk_ai.update(fatigue_score)

    if len(faces) > 0 and not calibration_complete:
        state = "CALIBRATING"
    elif fatigue_score > 70:
        state = "CRITICAL"
    elif fatigue_score > 40:
        state = "DROWSY"
    elif len(faces) > 0:
        state = "ALERT"
    else:
        state = "NO FACE IS THERE"

    if (
        calibration_complete
        and
        fatigue_score > 70
        and current_time - last_voice_time > voice_interval
    ):
        _speak_async("Critical fatigue detected. Please stop the vehicle.")
        last_voice_time = current_time
    elif (
        calibration_complete
        and
        fatigue_score > 40
        and current_time - last_voice_time > voice_interval
    ):
        _speak_async("Driver appears drowsy. Please stay alert.")
        last_voice_time = current_time

    if (
        phone_detected
        and current_time - last_voice_time > voice_interval
    ):
        _speak_async("Phone usage detected. Please keep your attention on the road.")
        last_voice_time = current_time

    if current_time - last_db_log_time > DB_LOG_INTERVAL:
        driver_database.log(
            driver_name,
            fatigue_score,
            state,
            ear,
            blink_rate,
            mar,
            attention_score,
            risk_score,
        )
        last_db_log_time = current_time

    # ---------------- Phone Box Drawing ----------------

    for (x1, y1, x2, y2) in phone_boxes:

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)

        cv2.putText(frame,
                    "PHONE DETECTED",
                    (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0,0,255),
                    2)

    # ---------------- Display Metrics ----------------
    # Create transparent dashboard panel
    overlay = frame.copy()

    cv2.rectangle(overlay, (10,10), (300,470), (0,0,0), -1)

    alpha = 0.4
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

# Dashboard title
    cv2.putText(frame,
            "DRIVER STATUS",
            (60,30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255,255,255),
            1)
    if 'ear' not in locals():
     ear = 0.0
    cv2.putText(frame, f"EAR: {ear:.2f}" if 'ear' in globals() or 'ear' in locals() else "EAR: 0.00",
            (20,40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.3,
            (0,255,0),
            1)

    cv2.putText(frame, f"PERCLOS: {perclos:.2f}", (20,70),
                cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,0,0),1)

    cv2.putText(frame, f"Blink Rate: {blink_rate:.1f}/min", (20,100),
                cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1)

    cv2.putText(frame, f"MAR: {mar:.2f}", (20,130),
                cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,0),1)

    cv2.putText(frame, f"Yawns: {total_yawns}", (20,160),
                cv2.FONT_HERSHEY_SIMPLEX,0.3,(200,200,255),1)

    cv2.putText(frame, f"Pitch: {pitch:.1f}", (20,190),
                cv2.FONT_HERSHEY_SIMPLEX,0.2,(255,255,255),1)

    cv2.putText(frame, f"Yaw: {yaw:.1f}", (20,220),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,255,255),2)

    cv2.putText(frame, f"Head: {head_state}", (20,250),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,100,100),2)

    cv2.putText(frame, f"State: {state}", (20,280),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),2)

    cv2.putText(frame, f"Fatigue Score: {fatigue_score}", (20,310),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,200),2)

    cv2.putText(frame, f"Attention Score: {attention_score}", (20,340),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,120),2)

    cv2.putText(frame, f"Gaze: {gaze_dir}", (20,370),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,200,0),2)   
# -------- Fatigue Forecast --------
    # -------- Fatigue Forecast --------
    if forecast_score is not None:

        cv2.putText(frame,
                f"Forecast Fatigue: {forecast_score}",
                (20,400),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255,150,0),
                2)
        if forecast_score > 70:
           cv2.putText(frame,
                    "FATIGUE WARNING COMING",
                    (20,430),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0,0,255),
                    2)   
        cv2.putText(frame,
            f"Accident Probability: {accident_prob}%",
            (20,540),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,0,255),
           2)
    if attention_score < 50:
        cv2.putText(frame, "DRIVER DISTRACTED", (20,400),
                    cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),2)

    if predicted_score is not None:

        cv2.putText(frame, f"Predicted Fatigue: {predicted_score}", (20,430),
                    cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,150,255),2)

        if predicted_score > 70:
            cv2.putText(frame, "EARLY WARNING: FATIGUE RISING", (20,460),
                        cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),2)

    cv2.putText(frame, f"Driver Risk: {risk_score}", (20,490),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,200,255),2)
    cv2.putText(frame,
            f"Driver: {driver_name}",
            (20,720),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,255,255),
            2)
    if risk_score > 75:
        cv2.putText(frame, "HIGH ACCIDENT RISK", (20,520),
                    cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),3)

    baseline_ear = driver_profile.baseline_ear()
    baseline_blink = driver_profile.baseline_blink()

    if baseline_ear is not None:
        cv2.putText(frame, f"Baseline EAR: {baseline_ear:.2f}", (20,550),
                    cv2.FONT_HERSHEY_SIMPLEX,0.5,(200,255,200),1)
        cv2.putText(frame, f"EAR Threshold: {dynamic_ear_threshold:.2f}", (20,575),
                    cv2.FONT_HERSHEY_SIMPLEX,0.5,(200,255,200),1)

    if baseline_blink is not None:
        cv2.putText(frame, f"Baseline Blink: {baseline_blink:.1f}", (20,600),
                    cv2.FONT_HERSHEY_SIMPLEX,0.4,(200,255,200),2)

    if future_fatigue is not None:

        cv2.putText(frame, f"Fatigue in 10s: {future_fatigue}", (20,625),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,150,0),2)
        # Prediction bar
        bar_x = 20
        bar_y = 650
        bar_width = 300
        bar_height = 20

# Draw background bar
        cv2.rectangle(frame,
              (bar_x, bar_y),
              (bar_x + bar_width, bar_y + bar_height),
              (50,50,50),
              -1)

# Fill bar based on predicted fatigue
        fill_width = int((future_fatigue / 100) * bar_width)

        cv2.rectangle(frame,
              (bar_x, bar_y),
              (bar_x + fill_width, bar_y + bar_height),
              (0,0,255),
              -1)

        cv2.putText(frame,
            "Future Fatigue Risk",
            (bar_x, bar_y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2)
        if future_fatigue > 75:
            cv2.putText(frame, "FATIGUE SPIKE EXPECTED", (20,640),
                        cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,0,255),3)

    if phone_detected:
     cv2.putText(frame, "DRIVER USING PHONE",
                (20,670),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0,0,255),
                3)

    cv2.putText(frame,
            "Database Logging Active",
            (20,760),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,100),
            2)

    cv2.putText(frame,
            "Press R to register new driver",
            (20,700),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255,255,0),
            2)

# ---------------- SHOW FRAME ----------------
    # ---------------- Fatigue Gauge ----------------

    gauge_center = (500, 380)
    radius = 80

# Draw outer circle
    cv2.circle(frame, gauge_center, radius, (200,200,200), 2)

# Draw colored zones
    cv2.ellipse(frame, gauge_center, (radius,radius), 0, 180, 240, (0,255,0), 6)   # ALERT
    cv2.ellipse(frame, gauge_center, (radius,radius), 0, 240, 300, (0,255,255), 6) # DROWSY
    cv2.ellipse(frame, gauge_center, (radius,radius), 0, 300, 360, (0,0,255), 6)   # CRITICAL

# Needle angle
    angle = 180 + int((fatigue_score / 100) * 180)

    needle_x = int(gauge_center[0] + radius * np.cos(np.radians(angle)))
    needle_y = int(gauge_center[1] + radius * np.sin(np.radians(angle)))

# Draw needle
    cv2.line(frame, gauge_center, (needle_x, needle_y), (255,255,255), 3)

# Gauge label
    cv2.putText(frame,
            "FATIGUE LEVEL",
            (440, 470),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255,255,255),
            1)
    if display_now - last_display_refresh > DISPLAY_REFRESH_INTERVAL:
        last_rendered_frame = frame.copy()
        last_display_refresh = display_now

    if last_rendered_frame is not None:
        cv2.imshow("Driver Monitoring System", last_rendered_frame)
    if SHOW_DEBUG_WINDOWS:
        if latest_heatmap is not None:
            cv2.imshow("Fatigue Heatmap", latest_heatmap)
        if latest_dashboard is not None:
            cv2.imshow("Fatigue Dashboard", latest_dashboard)
        if latest_live_graph is not None:
            cv2.imshow("Fatigue Trend", latest_live_graph)
        if latest_analytics is not None:
            cv2.imshow("Driver Analytics", latest_analytics)
# tiny sleep prevents CPU overload without adding visible lag
    time.sleep(0.005)
# ---------------- KEY EVENTS ----------------
    key = cv2.waitKey(1) & 0xFF

    if key == ord('r'):
      name = input("Enter driver name: ")
      driver_registration.register(frame, name)
      driver_recognition.load_drivers()
      driver_number_map = _build_driver_number_map()
      print("Driver registered successfully")

    if key == ord('p'):
       fatigue_report.generate()

    if key == 27:
        break

    # ---------------- Save Driver Session History ----------------

if len(session_scores) > 0:

    avg_session_score = sum(session_scores) / len(session_scores)

    driver_history.log(
        driver_name,
        avg_session_score,
        max_session_score,
        total_yawns
    )
# Outside the loop
cap.release()
cv2.destroyAllWindows()
