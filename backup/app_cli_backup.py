import cv2
import time
import logging
from config import Config
from mavlink.connection import MavlinkConnection
from mavlink.telemetry import Telemetry
from safety.safety_manager import SafetyManager
from ai.detector import ObjectDetector
from navigation.decision import DecisionModule

def main():
    print("========================================")
    print("  AUTONOMOUS DRONE SYSTEM INITIALIZING  ")
    print("========================================")
    
    # 1. Connect to Drone/SITL
    conn = MavlinkConnection(Config.CONNECTION_STRING, Config.BAUD_RATE)
    is_connected = conn.connect(timeout=5)
    
    # 2. Initialize Safety & Telemetry
    safety = SafetyManager(conn if is_connected else None)
    telemetry = Telemetry(conn) if is_connected else None
    
    # 3. Initialize AI & Decision Modules
    detector = ObjectDetector(model_path='yolov8n.pt')
    decision = DecisionModule(safety)
    
    # 4. Initialize Camera (Using webcam 0 for local testing)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Warning: Could not open camera.")
    
    print("\n--- SYSTEM READY ---")
    print("[!] Press 'q' in the camera window to exit.")
    
    # Example: Attempt a safe takeoff request (will prompt user for safety confirmation)
    if is_connected:
        safety.request_takeoff(altitude=5.0)
    else:
        print("[!] No drone connection. Running AI vision systems only.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
                
            # Run AI pipeline
            detections = detector.detect(frame)
            
            # Print Telemetry & Detections to terminal
            if is_connected:
                status = telemetry.get_status()
                pos = telemetry.get_position()
                print(f"[CONNECTED] | [ARMED: {status.get('armed')}] | [MODE: {status.get('mode')}] | [ALT: {pos.get('alt')}m]")
            
            # Pass data to Decision logic (which routes to Safety Manager)
            decision.process_detections(detections)
            
            # Display output (Visualizing YOLO)
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{det['class']} {det['confidence']:.2f}", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow("Drone Camera Feed", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nShutdown requested by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        conn.close()

if __name__ == "__main__":
    main()
