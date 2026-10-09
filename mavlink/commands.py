import time
import logging
from pymavlink import mavutil

logger = logging.getLogger(__name__)

class FlightCommands:
    def __init__(self, mav_connection):
        self.master = mav_connection.vehicle
        self.target_system = self.master.target_system
        self.target_component = self.master.target_component

    def arm(self):
        """Sends the ARM command to the drone."""
        logger.info("Sending ARM command...")
        self.master.mav.command_long_send(
            self.target_system, self.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 1, 0, 0, 0, 0, 0, 0 # 1 = Arm
        )

    def disarm(self):
        """Sends the DISARM command to the drone."""
        logger.info("Sending DISARM command...")
        self.master.mav.command_long_send(
            self.target_system, self.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 0, 0, 0, 0, 0, 0, 0 # 0 = Disarm
        )

    def takeoff(self, altitude):
        """Commands the drone to takeoff to a specific altitude."""
        logger.info(f"Sending TAKEOFF command to {altitude} meters...")
        self.master.mav.command_long_send(
            self.target_system, self.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0, 0, 0, 0, 0, 0, 0, altitude
        )

    def land(self):
        """Commands the drone to land at its current position."""
        logger.info("Sending LAND command...")
        self.master.mav.command_long_send(
            self.target_system, self.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND,
            0, 0, 0, 0, 0, 0, 0, 0
        )

    def return_to_launch(self):
        """Commands the drone to Return To Launch (RTL)."""
        logger.info("Sending RTL command...")
        self.master.mav.command_long_send(
            self.target_system, self.target_component,
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
            0, 0, 0, 0, 0, 0, 0, 0
        )
