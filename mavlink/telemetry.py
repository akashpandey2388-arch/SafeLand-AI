from pymavlink import mavutil

class Telemetry:
    def __init__(self, mav_connection):
        self.master = mav_connection.vehicle

    def get_status(self):
        """Fetches basic telemetry: armed state and flight mode."""
        if not self.master:
            return {"error": "Not connected"}
            
        # The heartbeat message contains armed state and mode
        msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=2)
        if msg:
            mode = mavutil.mode_string_v10(msg)
            is_armed = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
            return {
                "mode": mode,
                "armed": bool(is_armed)
            }
        return {"error": "No heartbeat data"}

    def get_position(self):
        """Fetches GPS latitude, longitude, altitude and heading."""
        if not self.master:
            return {"error": "Not connected"}
            
        # Request GLOBAL_POSITION_INT
        msg = self.master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=2)
        if msg:
            return {
                "lat": msg.lat / 1e7,
                "lon": msg.lon / 1e7,
                "alt": msg.relative_alt / 1000.0,  # meters
                "heading": msg.hdg / 100.0         # degrees
            }
        return {"error": "No GPS data"}

    def get_battery(self):
        """Fetches battery voltage and remaining percentage."""
        if not self.master:
            return {"error": "Not connected"}
            
        msg = self.master.recv_match(type='SYS_STATUS', blocking=True, timeout=2)
        if msg:
            return {
                "voltage": msg.voltage_battery / 1000.0, # Volts
                "remaining": msg.battery_remaining       # %
            }
        return {"error": "No battery data"}
