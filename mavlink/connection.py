import time
import logging
from pymavlink import mavutil

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class MavlinkConnection:
    def __init__(self, connection_string, baud_rate=115200):
        self.connection_string = connection_string
        self.baud_rate = baud_rate
        self.vehicle = None

    def connect(self, timeout=10):
        """Establishes connection to the flight controller and waits for heartbeat."""
        logger.info(f"Attempting connection on {self.connection_string}...")
        try:
            self.vehicle = mavutil.mavlink_connection(self.connection_string, baud=self.baud_rate)
            
            logger.info("Waiting for heartbeat...")
            heartbeat = self.vehicle.wait_heartbeat(timeout=timeout)
            
            if not heartbeat:
                logger.error("Connection failed: No heartbeat received.")
                return False
                
            logger.info(f"Heartbeat received! System ID: {self.vehicle.target_system} Component ID: {self.vehicle.target_component}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            return False

    def close(self):
        if self.vehicle:
            self.vehicle.close()
            logger.info("Connection closed.")
