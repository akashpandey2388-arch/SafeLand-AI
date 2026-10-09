import logging
from config import Config
from mavlink.commands import FlightCommands
from logs.flight_logger import flight_logger

logger = logging.getLogger(__name__)

class SafetyManager:
    def __init__(self, mav_connection):
        self.connection = mav_connection
        self.commander = FlightCommands(mav_connection) if mav_connection and mav_connection.vehicle else None
        self.emergency_triggered = False

    def request_arm(self, ui_confirmed=False):
        if not self.commander:
            logger.error("Cannot arm: No flight controller connection.")
            return False
            
        if Config.REQUIRE_CONFIRMATION and not ui_confirmed:
            logger.warning("Arming cancelled: UI confirmation required.")
            return False
            
        self.commander.arm()
        logger.info("Drone ARMED via Safety Manager.")
        return True

    def request_takeoff(self, altitude, ui_confirmed=False):
        if not self.commander:
            logger.error("Cannot takeoff: No flight controller connection.")
            return False
            
        if altitude > Config.MAX_ALTITUDE:
            logger.error(f"Takeoff aborted: Requested altitude {altitude}m exceeds max safety limit of {Config.MAX_ALTITUDE}m.")
            return False
            
        if Config.REQUIRE_CONFIRMATION and not ui_confirmed:
            logger.warning("Takeoff cancelled: UI confirmation required.")
            return False
            
        self.commander.takeoff(altitude)
        logger.info(f"TAKEOFF to {altitude}m initiated.")
        return True

    def trigger_emergency_land(self):
        """Emergency override. Does NOT require UI confirmation."""
        self.emergency_triggered = True
        logger.critical("EMERGENCY PROTOCOL: Initiating immediate landing.")
        if self.commander:
            self.commander.land()

    def trigger_rtl(self):
        """Emergency RTL. Does NOT require UI confirmation."""
        self.emergency_triggered = True
        logger.critical("EMERGENCY PROTOCOL: Returning to launch.")
        if self.commander:
            self.commander.return_to_launch()
