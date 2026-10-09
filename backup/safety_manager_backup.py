import logging
from config import Config
from mavlink.commands import FlightCommands

logger = logging.getLogger(__name__)

class SafetyManager:
    def __init__(self, mav_connection):
        self.connection = mav_connection
        self.commander = FlightCommands(mav_connection) if mav_connection and mav_connection.vehicle else None

    def _require_confirmation(self, action_name):
        """Forces terminal confirmation before executing dangerous commands."""
        if not Config.REQUIRE_CONFIRMATION:
            return True
            
        response = input(f"\n[SAFETY SYSTEM] WARNING: AI is attempting to {action_name}. Allow? (y/n): ")
        return response.strip().lower() == 'y'

    def request_arm(self):
        if not self.commander:
            logger.error("Cannot arm: No flight controller connection.")
            return False
            
        if self._require_confirmation("ARM the drone"):
            self.commander.arm()
            return True
        else:
            logger.info("Arming cancelled by safety manager.")
            return False

    def request_takeoff(self, altitude):
        if not self.commander:
            logger.error("Cannot takeoff: No flight controller connection.")
            return False
            
        if altitude > Config.MAX_ALTITUDE:
            logger.error(f"Takeoff aborted: Requested altitude {altitude}m exceeds max safety limit of {Config.MAX_ALTITUDE}m.")
            return False
            
        if self._require_confirmation(f"TAKEOFF to {altitude} meters"):
            self.commander.takeoff(altitude)
            return True
        else:
            logger.info("Takeoff cancelled by safety manager.")
            return False

    def trigger_emergency_land(self):
        """Emergency override. Does NOT require confirmation."""
        logger.warning("EMERGENCY PROTOCOL: Initiating immediate landing.")
        if self.commander:
            self.commander.land()

    def trigger_rtl(self):
        """Emergency RTL. Does NOT require confirmation."""
        logger.warning("EMERGENCY PROTOCOL: Returning to launch.")
        if self.commander:
            self.commander.return_to_launch()
