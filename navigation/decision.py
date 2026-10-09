import logging

logger = logging.getLogger(__name__)

class DecisionModule:
    def __init__(self, safety_manager):
        self.safety = safety_manager

    def process_detections(self, detections):
        """
        Reads AI detections and decides on flight actions.
        This isolates AI from direct flight control.
        """
        if not detections:
            return

        for det in detections:
            logger.info(f"AI Detected: {det['class']} (Conf: {det['confidence']:.2f}) at {det['bbox']}")
            
            # Example Logic: If we see a person, trigger emergency landing.
            if det['class'] == 'person':
                logger.critical("SAFETY BREACH: Person detected in flight path!")
                self.safety.trigger_emergency_land()
                break # Action taken, stop processing
