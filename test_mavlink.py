from config import Config
from mavlink.connection import MavlinkConnection
from mavlink.telemetry import Telemetry
import time

def run_test():
    print("--- AUTONOMOUS DRONE: PHASE 2 TEST ---")
    
    # 1. Connect
    conn = MavlinkConnection(Config.CONNECTION_STRING, Config.BAUD_RATE)
    success = conn.connect()
    
    if not success:
        print("\n[!] Connection failed. Please ensure ArduPilot SITL / Mission Planner is running.")
        print(f"[!] Currently trying to connect on: {Config.CONNECTION_STRING}")
        return

    # 2. Test Telemetry
    telemetry = Telemetry(conn)
    
    print("\nRequesting Telemetry Streams...")
    # Request data streams (to ensure Pixhawk starts sending data at regular intervals)
    conn.vehicle.mav.request_data_stream_send(
        conn.vehicle.target_system, 
        conn.vehicle.target_component,
        0, # req_stream_id (0 = all streams)
        2, # req_message_rate in Hz
        1  # start/stop
    )
    
    time.sleep(1) # wait for streams to populate
    
    print("\n--- TELEMETRY READOUT ---")
    
    status = telemetry.get_status()
    print(f"[MODE]: {status.get('mode', 'Unknown')}")
    print(f"[ARMED]: {status.get('armed', False)}")
    
    pos = telemetry.get_position()
    print(f"[GPS]: Lat {pos.get('lat', 'N/A')}, Lon {pos.get('lon', 'N/A')}")
    print(f"[ALTITUDE]: {pos.get('alt', 'N/A')} m")
    print(f"[HEADING]: {pos.get('heading', 'N/A')} deg")
    
    batt = telemetry.get_battery()
    print(f"[BATTERY]: {batt.get('voltage', 'N/A')}V ({batt.get('remaining', 'N/A')}%)")
    
    # 3. Clean disconnect
    print("\nTest complete. Closing connection.")
    conn.close()

if __name__ == "__main__":
    run_test()
