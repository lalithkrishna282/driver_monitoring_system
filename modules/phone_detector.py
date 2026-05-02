from ultralytics import YOLO
from pathlib import Path


class PhoneDetector:

    def __init__(self):
        model_path = Path(__file__).resolve().parents[1] / "yolov8n.pt"
        self.model = YOLO(str(model_path))
        # COCO class id for "cell phone"
        self.phone_class_id = 67

    def detect(self, frame):

        results = self.model.predict(
            source=frame,
            verbose=False,
            conf=0.30,
            iou=0.45,
            imgsz=320,
            classes=[self.phone_class_id],
        )

        phone_detected = False
        boxes = []

        for r in results:
            for box in r.boxes:

                cls = int(box.cls[0])
                label = self.model.names[cls]

                if cls == self.phone_class_id or str(label).lower() in {"cell phone", "mobile phone", "phone"}:
                    phone_detected = True
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    boxes.append((x1, y1, x2, y2))

        return phone_detected, boxes
