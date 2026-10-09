# config.py

class Config:
    # SITL Connection String (Mission Planner default TCP port for SITL is usually 5762 or 5763)
    # Alternatively, udp:127.0.0.1:14550 is common.
    CONNECTION_STRING = 'tcp:127.0.0.1:5762'
    BAUD_RATE = 115200
    
    # Safety settings
    REQUIRE_CONFIRMATION = True
    MAX_ALTITUDE = 10.0  # meters
