import logging
from ultralytics import YOLO
import cv2

logger = logging.getLogger(__name__)

class ObjectDetector:
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.5):
        """
        Initializes the YOLO object detector.
        Downloads the model automatically if 'yolov8n.pt' is not found locally.
        """
        logger.info(f"Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        """
        Runs inference on a single frame.
        Returns a list of dictionaries containing detection data.
        """
        if frame is None:
            return []

        # Run YOLO inference
        results = self.model(frame, verbose=False)[0]
        
        detections = []
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf >= self.conf_threshold:
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                
                # Bounding box coordinates [x1, y1, x2, y2]
                coords = box.xyxy[0].tolist()
                
                detections.append({
                    "class": class_name,
                    "confidence": conf,
                    "bbox": [int(c) for c in coords]
                })
                
        return detections
