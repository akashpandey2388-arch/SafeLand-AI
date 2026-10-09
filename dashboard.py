import streamlit as st
import cv2
import time
import pandas as pd
from datetime import datetime

# Import autonomous drone modules
from config import Config
from mavlink.connection import MavlinkConnection
from mavlink.telemetry import Telemetry
from safety.safety_manager import SafetyManager
from ai.detector import ObjectDetector
from navigation.decision import DecisionModule
from logs.flight_logger import flight_logger

# --- PAGE CONFIG ---
st.set_page_config(page_title="UAS Mission Control", page_icon="🛸", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Rajdhani:wght@500;600;700&display=swap');
    
    /* Typography Override */
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .stMetric, .metric-value { font-family: 'Rajdhani', sans-serif !important; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] { border-right: 1px solid #1e293b; }
    
    /* UAS Tactical Cards */
    .uas-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Status Badges */
    .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
    .badge-ok { background-color: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
    .badge-error { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
    .badge-warn { background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); }
    .badge-offline { background-color: rgba(100, 116, 139, 0.1); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.2); }

    /* Custom Metrics */
    .metric-label { font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
    .metric-value { font-size: 28px; color: #0ea5e9; line-height: 1.2; }
    .metric-value.safe { color: #10b981; }
    .metric-value.danger { color: #ef4444; }
    
    /* Buttons */
    .stButton>button { font-family: 'Rajdhani', sans-serif; font-size: 16px; font-weight: 600; letter-spacing: 1px; transition: all 0.3s ease; }
    
    /* Streamlit overrides for visual cleanliness */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- INIT SESSION STATE ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.is_connected = False
    st.session_state.conn = None
    st.session_state.safety = SafetyManager(None)
    st.session_state.telemetry = None
    st.session_state.detector = None
    st.session_state.decision = DecisionModule(st.session_state.safety)
    st.session_state.last_detections = []
    st.session_state.conf_threshold = 0.50

# --- HELPER FUNCTIONS ---
def draw_card(title, content):
    st.markdown(f'<div class="uas-card"><div class="metric-label">{title}</div>{content}</div>', unsafe_allow_html=True)

def draw_metric(label, value, status="normal"):
    color_class = ""
    if status == "safe": color_class = "safe"
    elif status == "danger": color_class = "danger"
    return f'''
    <div style="display: flex; flex-direction: column;">
        <span class="metric-label">{label}</span>
        <span class="metric-value {color_class}">{value}</span>
    </div>
    '''

def draw_badge(text, state):
    badge_class = "badge-offline"
    if state == "ok": badge_class = "badge-ok"
    elif state == "error": badge_class = "badge-error"
    elif state == "warn": badge_class = "badge-warn"
    return f'<span class="badge {badge_class}">{text}</span>'

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #0ea5e9; font-size: 24px;'>UAS COMMAND</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    page = st.radio("", ["Mission Readiness", "Payload & Sensors", "Flight Operations", "System Logs"], label_visibility="collapsed")
    
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<span class='metric-label'>System Integrity</span>", unsafe_allow_html=True)
    
    # Status Indicators in Sidebar
    mav_state = "ok" if st.session_state.is_connected else "offline"
    st.markdown(f"<div style='margin: 8px 0;'>MAVLink Link: {draw_badge('CONNECTED' if st.session_state.is_connected else 'OFFLINE', mav_state)}</div>", unsafe_allow_html=True)
    
    ai_state = "ok" if st.session_state.detector else "warn"
    st.markdown(f"<div style='margin: 8px 0;'>YOLOv8 Core: {draw_badge('ONLINE' if st.session_state.detector else 'STANDBY', ai_state)}</div>", unsafe_allow_html=True)

# ==========================================
# PAGE 1: MISSION READINESS (DASHBOARD)
# ==========================================
if page == "Mission Readiness":
    st.markdown("<h1>System Overview</h1>", unsafe_allow_html=True)
    
    # Top KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        draw_card("Link Status", draw_metric("MAVLink Protocol", "ACTIVE" if st.session_state.is_connected else "DISCONNECTED", "safe" if st.session_state.is_connected else "danger"))
    with col2:
        draw_card("AI Engine", draw_metric("YOLOv8 Inference", "READY" if st.session_state.detector else "STANDBY", "safe" if st.session_state.detector else "normal"))
    with col3:
        target_count = len(st.session_state.last_detections)
        draw_card("Live Targets", draw_metric("Tracking Objects", f"{target_count}", "normal" if target_count == 0 else "safe"))
    with col4:
        safety_text = "OVERRIDE" if st.session_state.safety.emergency_triggered else "SECURE"
        draw_card("Safety Status", draw_metric("Automated Guard", safety_text, "danger" if safety_text == "OVERRIDE" else "safe"))

    st.markdown("<h3>Pre-Flight Checklist</h3>", unsafe_allow_html=True)
    chk_col1, chk_col2 = st.columns(2)
    
    with chk_col1:
        st.markdown(f"""
        <div class="uas-card">
            <table style="width: 100%; text-align: left; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #1e293b;"><td style="padding: 12px 0; color: #e2e8f0;">Flight Controller Comm</td><td style="text-align: right;">{draw_badge("PASS", "ok") if st.session_state.is_connected else draw_badge("FAIL", "error")}</td></tr>
                <tr style="border-bottom: 1px solid #1e293b;"><td style="padding: 12px 0; color: #e2e8f0;">AI Model Weights loaded</td><td style="text-align: right;">{draw_badge("PASS", "ok") if st.session_state.detector else draw_badge("PENDING", "warn")}</td></tr>
                <tr><td style="padding: 12px 0; color: #e2e8f0;">Hardware Camera Mount</td><td style="text-align: right;">{draw_badge("UNKNOWN", "offline")}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with chk_col2:
        st.markdown(f"""
        <div class="uas-card">
            <div class="metric-label">Mission Parameters</div>
            <div style="color: #94a3b8; font-size: 14px; margin-top: 10px;">
                <b>Max Altitude Limit:</b> {Config.MAX_ALTITUDE}m <br>
                <b>Safety Confirmation:</b> {'ENABLED' if Config.REQUIRE_CONFIRMATION else 'DISABLED'} <br>
                <b>AI Confidence Threshold:</b> {st.session_state.conf_threshold * 100}% <br>
                <b>Primary Target:</b> 'person' -> Emergency Trigger
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 2: PAYLOAD & SENSORS (CAMERA)
# ==========================================
elif page == "Payload & Sensors":
    st.markdown("<h1>Payload & Visual Intelligence</h1>", unsafe_allow_html=True)
    
    col_video, col_data = st.columns([7, 3])
    
    with col_data:
        st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
        st.markdown("<span class='metric-label'>Sensor Controls</span>", unsafe_allow_html=True)
        start_cam = st.toggle("INITIALIZE OPTICAL SENSOR")
        
        st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
        det_count = st.empty()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Load AI if toggled
        if start_cam and not st.session_state.detector:
            with st.spinner("Initializing Deep Learning Core..."):
                try:
                    st.session_state.detector = ObjectDetector('yolov8n.pt', st.session_state.conf_threshold)
                except Exception as e:
                    st.error(f"Neural Engine Failure: {str(e)}")

        if st.session_state.safety.emergency_triggered:
            st.markdown(f'<div class="uas-card" style="border-color: #ef4444;">{draw_metric("CRITICAL ALERT", "EMERGENCY ENGAGED", "danger")}</div>', unsafe_allow_html=True)

    with col_video:
        frame_window = st.empty()
        
        if start_cam:
            cap = cv2.VideoCapture(0)
            try:
                if not cap.isOpened():
                    st.error("Hardware fault: Optical sensor unresponsive.")
                else:
                    while start_cam:
                        ret, frame = cap.read()
                        if not ret:
                            st.warning("Sensor sync lost. Retrying...")
                            time.sleep(0.5)
                            continue
                        
                        # AI Inference
                        if st.session_state.detector:
                            detections = st.session_state.detector.detect(frame)
                            st.session_state.last_detections = detections
                            st.session_state.decision.process_detections(detections)
                            
                            # Tactical HUD Drawing
                            for det in detections:
                                x1, y1, x2, y2 = det['bbox']
                                # Draw corners instead of full box for tactical feel
                                l = 15
                                color = (0, 255, 0) if det['class'] != 'person' else (0, 0, 255)
                                thickness = 2
                                # Top-left
                                cv2.line(frame, (x1, y1), (x1+l, y1), color, thickness)
                                cv2.line(frame, (x1, y1), (x1, y1+l), color, thickness)
                                # Top-right
                                cv2.line(frame, (x2, y1), (x2-l, y1), color, thickness)
                                cv2.line(frame, (x2, y1), (x2, y1+l), color, thickness)
                                # Bottom-left
                                cv2.line(frame, (x1, y2), (x1+l, y2), color, thickness)
                                cv2.line(frame, (x1, y2), (x1, y2-l), color, thickness)
                                # Bottom-right
                                cv2.line(frame, (x2, y2), (x2-l, y2), color, thickness)
                                cv2.line(frame, (x2, y2), (x2, y2-l), color, thickness)
                                
                                cv2.putText(frame, f"ID: {det['class'].upper()} [{det['confidence']:.2f}]", (x1, y1-10), 
                                            cv2.FONT_HERSHEY_PLAIN, 1.2, color, 2)
                        else:
                            detections = []
                        
                        # Apply subtle grid overlay for HUD effect
                        h, w = frame.shape[:2]
                        cv2.line(frame, (w//2, 0), (w//2, h), (255, 255, 255), 1, lineType=cv2.LINE_4)
                        cv2.line(frame, (0, h//2), (w, h//2), (255, 255, 255), 1, lineType=cv2.LINE_4)
                        
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_window.image(frame, channels="RGB", use_container_width=True)
                        
                        # Update stats
                        det_count.markdown(draw_metric("Active Track Signatures", len(detections), "safe" if len(detections)>0 else "normal"), unsafe_allow_html=True)
                        
                        time.sleep(0.05)
            finally:
                cap.release()
        else:
            frame_window.markdown("""
            <div style="height: 400px; background-color: #0f172a; border: 1px solid #1e293b; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                <h3 style="color: #64748b; font-family: 'Rajdhani', sans-serif; letter-spacing: 2px;">OPTICAL SENSOR OFFLINE</h3>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# PAGE 3: FLIGHT OPERATIONS
# ==========================================
elif page == "Flight Operations":
    st.markdown("<h1>Flight Operations</h1>", unsafe_allow_html=True)
    
    col_cmd, col_tel = st.columns([4, 6])
    
    with col_cmd:
        st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
        st.markdown("<span class='metric-label'>Uplink Control</span>", unsafe_allow_html=True)
        
        if not st.session_state.is_connected:
            if st.button("ESTABLISH MAVLINK"):
                with st.spinner("Handshaking..."):
                    conn = MavlinkConnection(Config.CONNECTION_STRING, Config.BAUD_RATE)
                    if conn.connect(timeout=5):
                        st.session_state.conn = conn
                        st.session_state.is_connected = True
                        st.session_state.telemetry = Telemetry(conn)
                        st.session_state.safety = SafetyManager(conn)
                        st.session_state.decision.safety = st.session_state.safety
                        st.rerun()
                    else:
                        st.error("Uplink Failed.")
        else:
            if st.button("SEVER LINK", type="primary"):
                st.session_state.conn.close()
                st.session_state.is_connected = False
                st.rerun()
                
        st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
        st.markdown("<span class='metric-label'>Tactical Commands</span>", unsafe_allow_html=True)
        confirm = st.checkbox("UNLOCK FLIGHT CONTROLS")
        
        st.button("ARM PROPULSION", disabled=not (confirm and st.session_state.is_connected), on_click=lambda: st.session_state.safety.request_arm(ui_confirmed=True))
        st.button("INITIATE TAKEOFF (5m)", disabled=not (confirm and st.session_state.is_connected), on_click=lambda: st.session_state.safety.request_takeoff(altitude=5.0, ui_confirmed=True))
        st.button("AUTO-LAND", disabled=not st.session_state.is_connected, on_click=lambda: st.session_state.safety.commander.land())
        st.button("RETURN TO BASE (RTL)", disabled=not st.session_state.is_connected, on_click=lambda: st.session_state.safety.commander.return_to_launch())
        st.markdown("</div>", unsafe_allow_html=True)

    with col_tel:
        st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
        st.markdown("<span class='metric-label'>Live Telemetry</span>", unsafe_allow_html=True)
        
        if st.session_state.is_connected:
            status = st.session_state.telemetry.get_status()
            pos = st.session_state.telemetry.get_position()
            batt = st.session_state.telemetry.get_battery()
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(draw_metric("ARM STATE", "ARMED" if status.get('armed') else "DISARMED", "safe" if status.get('armed') else "normal"), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(draw_metric("FLIGHT MODE", status.get('mode', 'UNK')), unsafe_allow_html=True)
            with c2:
                st.markdown(draw_metric("ALTITUDE", f"{pos.get('alt', 0):.2f}m", "safe"), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(draw_metric("HEADING", f"{pos.get('heading', 0):.1f}°"), unsafe_allow_html=True)
            with c3:
                st.markdown(draw_metric("BATTERY", f"{batt.get('remaining', 0)}%", "safe" if batt.get('remaining', 0) > 20 else "danger"), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(draw_metric("VOLTAGE", f"{batt.get('voltage', 0):.2f}V"), unsafe_allow_html=True)
        else:
            st.info("NO TELEMETRY DATA (Link Offline)")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# PAGE 4: SYSTEM LOGS
# ==========================================
elif page == "System Logs":
    st.markdown("<h1>Flight Recorder & Logs</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
    logs = flight_logger.get_logs_df()
    if not logs.empty:
        st.dataframe(logs.tail(100), use_container_width=True)
        csv = logs.to_csv(index=False).encode('utf-8')
        st.download_button("Export Flight Data (CSV)", csv, "blackbox_logs.csv", "text/csv")
    else:
        st.info("Blackbox empty. No records found.")
    st.markdown("</div>", unsafe_allow_html=True)
