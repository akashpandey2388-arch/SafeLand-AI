# 🛰️ Autonomous Drone AI — UAS Mission Control & C2 Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![MAVLink](https://img.shields.io/badge/Protocol-MAVLink%202.0-0ea5e9)](https://mavlink.io/en/)
[![YOLOv8](https://img.shields.io/badge/AI-Ultralytics%20YOLOv8-10b981?logo=yolo)](https://github.com/ultralytics/ultralytics)
[![ArduPilot](https://img.shields.io/badge/Firmware-ArduPilot%20%2F%20SITL-orange)](https://ardupilot.org/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An enterprise-grade autonomous unmanned aerial system (UAS) command-and-control (C2) software platform. Built with Python, OpenCV, YOLOv8 computer vision, and PyMAVLink for real-time telemetry streaming and guarded mission execution on ArduPilot flight controllers and SITL simulations.

---

## 📑 Table of Contents
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [SITL Simulation Testing](#-sitl-simulation-testing)
- [Safety Interlocks & Fail-Safes](#-safety-interlocks--fail-safes)
- [Contributing & License](#-license)

---

## 🌟 Key Features

- **🛸 Tactical C2 Aerospace Dashboard:** Modern dark-themed tactical command terminal with Google Fonts (`Rajdhani`, `Share Tech Mono`), status pills, and glassmorphic telemetry cards.
- **👁️ Neural Object Detection (YOLOv8):** Real-time computer vision identifying humans, vehicles, and landing zone hazards with configurable confidence thresholds.
- **🎯 Military-Style Optical HUD:** Low-latency OpenCV video feed featuring corner targeting brackets, lock-on vectors to frame center, and crosshair overlays.
- **🛡️ Deterministic Safety Guard:** Hardware interlocks preventing accidental propulsion arming or takeoff. Automated threat classification triggers emergency RTL (Return to Launch) or LAND if a human is detected in the landing corridor.
- **📡 MAVLink 2.0 Bi-Directional Uplink:** Direct telemetry parsing for barometric altitude, 3D GPS fixes, compass heading, battery voltage, and flight modes.
- **🎬 Native 30-Sec Aerial Reconnaissance Replay:** Integrated onboard optical sensor video playback loop with zero external third-party watermarks.
- **📋 Blackbox Flight Logger:** In-memory structured telemetry event logging with instantaneous CSV export for post-flight debriefs.

---

## 🏗️ System Architecture

```
                    ┌─────────────────┐
                    │  CAMERA STREAM  │
                    │  (USB / RTSP)   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  YOLOv8 NEURAL  │
                    │ OBJECT DETECTOR │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ DECISION ENGINE │
                    │ Threat Analysis │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ SAFETY MANAGER  │
                    │ UI Interlocks   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  PYMAVLINK C2   │
                    │ Packets/Commands│
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │ ARDUPILOT FLIGHT CONTROLLER  │
              │   (Pixhawk / Cube / SITL)    │
              └──────────────┬───────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ PHYSICAL DRONE  │
                    └─────────────────┘
```

---

## 📂 Project Structure

```
autonomous_drone/
├── .streamlit/
│   └── config.toml             # Dark aerospace UI theme configuration
├── ai/
│   ├── detector.py             # Ultralytics YOLOv8 inference wrapper
│   └── tracker.py              # Visual multi-object tracker
├── assets/
│   └── drone_recon_30s.mp4     # 30-second native reconnaissance video
├── logs/
│   └── flight_logger.py        # In-memory blackbox logger & CSV generator
├── mavlink/
│   ├── commands.py             # Guarded flight commands (arm, takeoff, land, RTL)
│   ├── connection.py           # PyMAVLink serial/TCP/UDP connection handler
│   └── telemetry.py            # Real-time state and telemetry parser
├── navigation/
│   └── decision.py             # AI detection to safety protocol mapper
├── safety/
│   └── safety_manager.py       # Hardware safety interlocks & override gates
├── app.py                      # Core CLI application entry-point
├── config.py                   # Centralized configuration & parameters
├── dashboard.py                # Streamlit C2 Web Dashboard & Landing Page
├── requirements.txt            # Python dependencies
├── test_mavlink.py             # Unit tests for MAVLink connection
└── yolov8n.pt                  # Pre-trained YOLOv8 Nano weights
```

---

## 💻 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/akashpandey2388-arch/SafeLand-AI.git
cd SafeLand-AI
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### Launch the C2 Web Dashboard
Start the tactical browser application locally:
```bash
python -m streamlit run dashboard.py
```
Open **`http://localhost:8501`** in your browser.

- Navigate through **"Overview (Landing Page)"**, **"Optical Sensor HUD"**, and **"Flight Ops & Telemetry"** using the sidebar.
- Toggle **"ACTIVATE CAMERA STREAM"** to run local YOLOv8 inference with tactical overlays directly on your webcam.

---

## 🎮 SITL Simulation Testing

To test autonomous commands without physical hardware:

1. Launch ArduPilot Software-In-The-Loop (SITL):
   ```bash
   sim_vehicle.py -v ArduCopter -f quad --console --map
   ```
2. In `config.py`, verify the connection string:
   ```python
   CONNECTION_STRING = "tcp:127.0.0.1:5762" # Default ArduPilot SITL TCP port
   ```
3. In the C2 Dashboard under **"Flight Ops & Telemetry"**, click **"INITIALIZE MAVLINK"**.
4. Check **"DEACTIVATE SAFETY INTERLOCK"** to unlock propulsion arming and takeoff triggers.

---

## 🛡️ Safety Interlocks & Fail-Safes

- **Guarded Propulsion Arming:** No physical motor can spin without explicit operator UI interlock confirmation.
- **Altitude Ceilings:** Strictly enforced maximum climb limits configured in `config.py` (default: 10.0m).
- **Collision Threat Interlock:** Detection of a human or critical hazard inside the landing zone immediately triggers an emergency protocol overriding manual input to command **AUTO-LAND** or **RTL**.
- **Heartbeat Timeout Protection:** Automatic telemetry stream invalidation if heartbeat messages cease for more than 3 seconds.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Engineered for Autonomous Robotics, Computer Vision Research, and Mission Readiness.*
