import os
import cv2
import numpy as np
from ultralytics import YOLO

class ObstacleDetector:
    def __init__(self, model_name="yolov8n.pt", confidence_threshold=0.4):
        """
        Initializes the YOLOv8 obstacle detector.
        Downloads the model to the 'models' directory if not already present.
        """
        self.conf_threshold = confidence_threshold
        
        # Ensure the models directory exists
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        os.makedirs(models_dir, exist_ok=True)
        
        model_path = os.path.join(models_dir, model_name)
        
        # Initialize YOLOv8 model (downloads automatically if not found at model_path)
        print(f"Loading YOLOv8 model: {model_name}...")
        self.model = YOLO(model_path)
        
        # COCO Class mapping helper
        # Classes of interest:
        # Person: 0
        # Vehicles: 1 (bicycle), 2 (car), 3 (motorcycle), 5 (bus), 7 (truck), 8 (boat)
        # Animals: 14 (bird), 15 (cat), 16 (dog), 17 (horse), 18 (sheep), 19 (cow)
        # Common Obstacles: 13 (bench), 24 (backpack), 25 (umbrella), 26 (handbag), 28 (suitcase), 
        #                   56 (chair), 57 (couch), 60 (dining table)
        # Vegetation: 58 (potted plant)
        
        self.vehicle_classes = {1, 2, 3, 5, 7, 8}
        self.animal_classes = {14, 15, 16, 17, 18, 19}
        self.obstacle_classes = {13, 24, 25, 26, 28, 56, 57, 60}
        self.vegetation_classes = {58}

    def detect(self, frame):
        """
        Runs object detection on a single frame.
        Returns a list of detections: 
        [
            {
                "bbox": [x1, y1, x2, y2], # normalized coords or raw coords depending on usage.
                "class_id": int,
                "label": str,
                "confidence": float,
                "category": str # 'DANGEROUS', 'CAUTION'
            },
            ...
        ]
        """
        if frame is None:
            return []
            
        results = self.model(frame, verbose=False)[0]
        detections = []
        
        # Retrieve bboxes, confs, and class IDs
        boxes = results.boxes
        for box in boxes:
            conf = float(box.conf[0])
            if conf < self.conf_threshold:
                continue
                
            class_id = int(box.cls[0])
            label = self.model.names[class_id]
            
            # Extract coordinates [x1, y1, x2, y2]
            coords = box.xyxy[0].tolist()
            x1, y1, x2, y2 = map(int, coords)
            
            # Categorize the detection for landing safety
            category = "CAUTION"  # Default category
            friendly_name = label.capitalize()
            
            if class_id == 0:
                category = "DANGEROUS"
                friendly_name = "Person"
            elif class_id in self.vehicle_classes:
                category = "DANGEROUS"
                friendly_name = f"Vehicle ({label.capitalize()})"
            elif class_id in self.animal_classes:
                category = "DANGEROUS"
                friendly_name = f"Animal ({label.capitalize()})"
            elif class_id in self.obstacle_classes:
                category = "DANGEROUS"
                friendly_name = label.capitalize()
            elif class_id in self.vegetation_classes:
                category = "CAUTION"
                friendly_name = "Vegetation/Tree"
                
            detections.append({
                "bbox": [x1, y1, x2, y2],
                "class_id": class_id,
                "label": label,
                "friendly_name": friendly_name,
                "confidence": conf,
                "category": category
            })
            
        return detections
