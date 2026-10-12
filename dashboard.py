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
st.set_page_config(
    page_title="Autonomous Drone AI | Aerial Intelligence Platform",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- HYPER-PROFESSIONAL AEROSPACE & CINEMATIC CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;500;600;700&family=Rajdhani:wght@500;600;700;800&display=swap');
    
    html {
        scroll-behavior: smooth;
    }
    
    /* Base Body & Layout */
    html, body, [class*="st-"] {
        font-family: 'Inter', -apple-system, sans-serif;
        background-color: #050810;
        color: #94a3b8;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Rajdhani', sans-serif !important;
        color: #f8fafc;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 0.5rem;
    }
    
    .tech-font {
        font-family: 'Share Tech Mono', monospace;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #070c18 !important;
        border-right: 1px solid rgba(14, 165, 233, 0.2);
    }
    
    /* Global Container */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px;
    }
    
    /* Navbar Banner */
    .nav-banner {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 24px;
        background: rgba(11, 19, 38, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 8px;
        margin-bottom: 25px;
    }
    
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .nav-logo-text {
        font-family: 'Rajdhani', sans-serif;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 2px;
        color: #38bdf8;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
    }
    
    .nav-links {
        display: flex;
        gap: 20px;
        font-size: 13px;
        font-weight: 500;
    }
    
    .nav-links a {
        color: #94a3b8;
        text-decoration: none;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .nav-links a:hover {
        color: #38bdf8;
        text-shadow: 0 0 8px rgba(56, 189, 248, 0.6);
    }

    /* Hero Section */
    .hero-container {
        position: relative;
        padding: 35px 30px;
        background: radial-gradient(circle at 80% 20%, rgba(14, 165, 233, 0.15) 0%, rgba(15, 23, 42, 0.7) 60%, rgba(5, 8, 16, 0.95) 100%),
                    linear-gradient(180deg, rgba(8, 14, 28, 0.8) 0%, rgba(5, 8, 16, 0.95) 100%);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-top: 3px solid #0ea5e9;
        border-radius: 14px;
        margin-bottom: 30px;
        overflow: hidden;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.8), 0 0 30px rgba(14, 165, 233, 0.1);
    }
    
    .hero-grid {
        display: grid;
        grid-template-columns: 1.15fr 1fr;
        gap: 28px;
        align-items: center;
    }
    
    @media (max-width: 1024px) {
        .hero-grid {
            grid-template-columns: 1fr;
        }
    }
    
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 5px 12px;
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 4px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 11px;
        color: #38bdf8;
        letter-spacing: 2px;
        margin-bottom: 12px;
        text-transform: uppercase;
    }
    
    .hero-headline {
        font-family: 'Share Tech Mono', monospace;
        font-size: 14px;
        color: #14b8a6;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    
    .hero-title {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 46px !important;
        font-weight: 800 !important;
        letter-spacing: 2px;
        line-height: 1.05;
        background: linear-gradient(120deg, #ffffff 30%, #38bdf8 70%, #14b8a6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 14px;
    }
    
    .hero-desc {
        font-size: 16px;
        line-height: 1.6;
        color: #cbd5e1;
        margin-bottom: 24px;
    }
    
    .hero-video-box {
        background: #020617;
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 0 25px rgba(14, 165, 233, 0.25), 0 15px 35px rgba(0, 0, 0, 0.9);
    }
    
    .hero-video-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 14px;
        background: rgba(15, 23, 42, 0.95);
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        font-family: 'Share Tech Mono', monospace;
        font-size: 11px;
        color: #38bdf8;
        letter-spacing: 1px;
    }
    
    .hero-video-embed {
        position: relative;
        padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
        height: 0;
        overflow: hidden;
        background: #000;
    }
    
    .hero-video-embed iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 0;
    }
    
    .hero-cta-group {
        display: flex;
        gap: 14px;
        align-items: center;
        flex-wrap: wrap;
    }
    
    .btn-hero-primary {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 12px 26px;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff !important;
        font-family: 'Rajdhani', sans-serif;
        font-size: 17px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        text-decoration: none !important;
        border: 1px solid #38bdf8;
        border-radius: 6px;
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.4);
        transition: all 0.25s ease;
    }
    
    .btn-hero-primary:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.7);
        transform: translateY(-2px);
    }
    
    .btn-hero-secondary {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 12px 26px;
        background: rgba(15, 23, 42, 0.8);
        color: #38bdf8 !important;
        font-family: 'Rajdhani', sans-serif;
        font-size: 17px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        text-decoration: none !important;
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 6px;
        transition: all 0.25s ease;
    }
    
    .btn-hero-secondary:hover {
        background: rgba(56, 189, 248, 0.15);
        border-color: #38bdf8;
        transform: translateY(-2px);
    }

    /* Video Section Box */
    .video-section-box {
        background: linear-gradient(180deg, #0b1329 0%, #070c19 100%);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-top: 3px solid #14b8a6;
        border-radius: 14px;
        padding: 30px;
        margin-bottom: 40px;
        box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.7), 0 0 25px rgba(20, 184, 166, 0.08);
    }
    
    .video-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 15px;
    }
    
    .video-frame-wrap {
        position: relative;
        padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
        height: 0;
        overflow: hidden;
        border-radius: 10px;
        border: 1px solid rgba(56, 189, 248, 0.25);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.8);
        background: #000000;
    }
    
    .video-frame-wrap iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 0;
    }
    
    .video-meta-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 15px;
        padding: 12px 18px;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        font-size: 13px;
        flex-wrap: wrap;
        gap: 10px;
    }

    /* Feature Cards Grid */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px;
        margin-bottom: 40px;
    }
    
    .feature-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(6, 11, 23, 0.95) 100%);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-left: 3px solid #0ea5e9;
        border-radius: 10px;
        padding: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.45);
        box-shadow: 0 12px 25px -8px rgba(14, 165, 233, 0.2);
    }
    
    .feature-icon-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border-radius: 8px;
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        font-size: 20px;
        margin-bottom: 16px;
    }
    
    .feature-title {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 21px !important;
        font-weight: 700;
        color: #f1f5f9;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .feature-desc {
        font-size: 14px;
        line-height: 1.6;
        color: #94a3b8;
        margin-bottom: 16px;
    }
    
    .feature-status {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: 'Share Tech Mono', monospace;
        font-size: 11px;
        color: #64748b;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        padding-top: 12px;
    }

    /* Overview Status Cards */
    .status-overview-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
        margin-bottom: 35px;
    }
    
    .uas-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(5, 8, 16, 0.95) 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-top: 2px solid rgba(56, 189, 248, 0.6);
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 8px 20px -8px rgba(0, 0, 0, 0.7);
        position: relative;
    }
    
    .metric-label {
        font-size: 11px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 26px;
        color: #e0f2fe;
        font-family: 'Share Tech Mono', monospace;
        line-height: 1.1;
    }
    
    .metric-value.safe { color: #34d399; text-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }
    .metric-value.danger { color: #f87171; text-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }
    .metric-value.standby { color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.4); }

    /* Badges & Pulsing Lights */
    .badge {
        padding: 4px 10px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-radius: 4px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-ok { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-error { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-warn { background: rgba(245, 158, 11, 0.1); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-offline { background: rgba(100, 116, 139, 0.1); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }

    @keyframes pulse-green { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }
    @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; }
    .dot-green { background-color: #10b981; animation: pulse-green 2s infinite; }
    .dot-red { background-color: #ef4444; animation: pulse-red 2s infinite; }
    .dot-gray { background-color: #64748b; }

    /* Footer styling */
    .landing-footer {
        border-top: 1px solid rgba(56, 189, 248, 0.2);
        padding-top: 30px;
        margin-top: 50px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 20px;
        font-size: 13px;
        color: #64748b;
    }

    /* Buttons inside Streamlit */
    .stButton>button {
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 1.5px;
        background: rgba(15, 23, 42, 0.9);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 4px;
        text-transform: uppercase;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: rgba(14, 165, 233, 0.2);
        border-color: #38bdf8;
        color: #ffffff;
        box-shadow: 0 0 12px rgba(14, 165, 233, 0.3);
    }
    
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
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

# --- UI HELPERS ---
def draw_badge(text, state):
    badge_class = {"ok": "badge-ok", "error": "badge-error", "warn": "badge-warn"}.get(state, "badge-offline")
    dot_class = {"ok": "dot-green", "error": "dot-red", "warn": "dot-red"}.get(state, "dot-gray")
    return f'<span class="badge {badge_class}"><span class="dot {dot_class}"></span>{text}</span>'

# --- TOP NAVIGATION BAR ---
st.markdown("""
<div class="nav-banner">
    <div class="nav-brand">
        <span style="font-size: 26px;">🛰️</span>
        <span class="nav-logo-text">AUTONOMOUS DRONE AI</span>
    </div>
    <div class="nav-links">
        <a href="#home">Home</a>
        <a href="#overview">Status</a>
        <a href="#drone-video">Live Video</a>
        <a href="#features">Technology</a>
        <a href="#contact">Contact</a>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-size: 24px; color: #38bdf8; margin-bottom: 0;'>UAS FLIGHT CORE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: \"Share Tech Mono\"; font-size: 11px; color: #64748b; margin-top: -6px;'>AUTONOMOUS C2 PLATFORM</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(56,189,248,0.2);'>", unsafe_allow_html=True)
    
    page = st.radio(
        "Module Select",
        [
            "🏠 Overview (Landing Page)",
            "👁️ Optical Sensor HUD",
            "🎮 Flight Ops & Telemetry",
            "📋 Blackbox Logs",
            "⚙️ Mission Diagnostics"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("<hr style='border-color: rgba(56,189,248,0.2);'>", unsafe_allow_html=True)
    st.markdown("<span class='tech-font' style='font-size:11px; color:#38bdf8; letter-spacing:1px;'>REAL HARDWARE LINK</span>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='margin: 8px 0; display:flex; justify-content:space-between; align-items:center;'><span class='tech-font' style='font-size:12px;'>MAVLINK UPLINK</span> {draw_badge('ACTIVE' if st.session_state.is_connected else 'OFFLINE', 'ok' if st.session_state.is_connected else 'error')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin: 8px 0; display:flex; justify-content:space-between; align-items:center;'><span class='tech-font' style='font-size:12px;'>YOLOv8 ENGINE</span> {draw_badge('READY' if st.session_state.detector else 'STANDBY', 'ok' if st.session_state.detector else 'warn')}</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.info("💡 Tip: Click 'Optical Sensor HUD' to activate your webcam & live YOLO inference.")


# ==========================================
# PAGE 1: OVERVIEW & LANDING PAGE
# ==========================================
if page == "🏠 Overview (Landing Page)":
    
    # 1. HERO SECTION WITH RUNNING 30-SEC DRONE VIDEO
    st.markdown('<div id="home"></div><div id="drone-video"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero-container">
        <div class="hero-grid">
            <div>
                <div class="hero-badge">
                    <span class="dot dot-green"></span> SYSTEM READY // ARDUPILOT & SITL COMPATIBLE
                </div>
                <div class="hero-headline">INTELLIGENCE IN THE SKY</div>
                <div class="hero-title">Autonomous Drone AI</div>
                <div class="hero-desc">
                    Intelligent aerial monitoring powered by computer vision, real-time object detection, and safety-aware automation. Built for mission readiness in research, inspection, and autonomous navigation.
                </div>
                <div class="hero-cta-group">
                    <a href="#features" class="btn-hero-primary">
                        ⚙ Explore Technology
                    </a>
                    <a href="https://youtu.be/VucKgyB_RmI?si=W_RITDWDm3poYe2Z" target="_blank" class="btn-hero-secondary">
                        ↗ Full YouTube Stream
                    </a>
                </div>
            </div>
            <div>
                <div class="hero-video-box">
                    <div class="hero-video-topbar">
                        <span style="display:flex; align-items:center; gap:6px;">
                            <span class="dot dot-red"></span> LIVE AERIAL STREAM // 30s RECON
                        </span>
                        <span>1080p 60FPS</span>
                    </div>
                    <div class="hero-video-embed">
                        <iframe 
                            src="https://www.youtube.com/embed/VucKgyB_RmI?autoplay=1&mute=1&loop=1&playlist=VucKgyB_RmI&start=0&end=30&controls=1&rel=0&modestbranding=1&enablejsapi=1" 
                            title="Autonomous Drone Aerial Intelligence" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                            allowfullscreen>
                        </iframe>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Action trigger bar (Launch operational tools)
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("🚀 LAUNCH OPTICAL SENSOR HUD"):
            st.session_state["nav_jump"] = "👁️ Optical Sensor HUD"
            st.info("Select '👁️ Optical Sensor HUD' in the left sidebar to activate.")
    with q2:
        if st.button("📡 CONNECT MAVLINK TELEMETRY"):
            st.session_state["nav_jump"] = "🎮 Flight Ops & Telemetry"
            st.info("Select '🎮 Flight Ops & Telemetry' in the left sidebar to connect.")
    with q3:
        if st.button("📑 VIEW SYSTEM BLACKBOX"):
            st.info("Select '📋 Blackbox Logs' in the left sidebar to export CSV.")

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # 2. SYSTEM OVERVIEW SECTION (True Real Status)
    st.markdown('<div id="overview"></div>', unsafe_allow_html=True)
    st.markdown("<h3>Live System Integrity</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:14px; margin-top:-8px; margin-bottom:18px;'>Actual hardware state from local controllers and neural engines. No fabricated data.</p>", unsafe_allow_html=True)
    
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        is_conn = st.session_state.is_connected
        st.markdown(f"""
        <div class="uas-card">
            <div class="metric-label">Drone Connection</div>
            <div class="metric-value {'safe' if is_conn else 'danger'}">{'CONNECTED' if is_conn else 'DISCONNECTED'}</div>
            <div style="margin-top: 10px;">{draw_badge('ONLINE' if is_conn else 'OFFLINE', 'ok' if is_conn else 'error')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with s_col2:
        has_ai = st.session_state.detector is not None
        st.markdown(f"""
        <div class="uas-card">
            <div class="metric-label">AI Neural Engine</div>
            <div class="metric-value {'safe' if has_ai else 'standby'}">{'YOLOv8 READY' if has_ai else 'STANDBY'}</div>
            <div style="margin-top: 10px;">{draw_badge('INFERENCE ACTIVE' if has_ai else 'ON DEMAND', 'ok' if has_ai else 'warn')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with s_col3:
        target_count = len(st.session_state.last_detections)
        st.markdown(f"""
        <div class="uas-card">
            <div class="metric-label">Camera & Vision</div>
            <div class="metric-value {'safe' if target_count > 0 else 'standby'}">{f'{target_count} TARGETS' if target_count > 0 else 'STANDBY'}</div>
            <div style="margin-top: 10px;">{draw_badge('OPENCV HUD' if target_count > 0 else 'READY TO MOUNT', 'ok' if target_count > 0 else 'offline')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with s_col4:
        is_emergency = st.session_state.safety.emergency_triggered
        st.markdown(f"""
        <div class="uas-card">
            <div class="metric-label">Safety Monitor</div>
            <div class="metric-value {'danger' if is_emergency else 'safe'}">{'OVERRIDE' if is_emergency else 'SECURE'}</div>
            <div style="margin-top: 10px;">{draw_badge('THREAT DETECTED' if is_emergency else 'NOMINAL', 'error' if is_emergency else 'ok')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # 3. YOUTUBE VIDEO SECTION (Embedded Directly into Homepage)
    st.markdown('<div id="drone-video"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="video-section-box">
        <div class="video-header">
            <div>
                <div style="font-family: 'Share Tech Mono', monospace; font-size: 12px; color: #14b8a6; letter-spacing: 2px;">
                    FIELD OPERATIONS // 30-SEC AERIAL RECONNAISSANCE
                </div>
                <h2 style="margin: 0; font-size: 32px; color: #f8fafc;">Live Aerial Intelligence</h2>
                <p style="color: #94a3b8; font-size: 15px; margin: 4px 0 0 0;">
                    30-second high-definition autonomous aerial reconnaissance, flight vectors, and target scanning.
                </p>
            </div>
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <span class="badge badge-ok">
                    ⏱️ 30 SEC DURATION
                </span>
                <span class="badge badge-warn">
                    <span class="dot dot-red"></span> DEMO FOOTAGE
                </span>
            </div>
        </div>
        
        <div class="video-frame-wrap">
            <iframe 
                src="https://www.youtube.com/embed/VucKgyB_RmI?start=0&end=30&rel=0&modestbranding=1&enablejsapi=1" 
                title="Autonomous Drone Aerial Intelligence" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                allowfullscreen>
            </iframe>
        </div>
        
        <div class="video-meta-bar">
            <div style="display: flex; gap: 18px; align-items: center; color: #cbd5e1; font-family: 'Share Tech Mono', monospace; font-size: 12px;">
                <span>DURATION: <b>0:30 (30 SECONDS)</b></span>
                <span>•</span>
                <span>FPS: <b>60</b></span>
                <span>•</span>
                <span>RESOLUTION: <b>1080p FHD</b></span>
                <span>•</span>
                <span>SOURCE: <b>AUTONOMOUS UAS LOG ARCHIVE</b></span>
            </div>
            <div>
                <a href="https://youtu.be/VucKgyB_RmI?si=W_RITDWDm3poYe2Z" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
                    ↗ Open Full Video on YouTube
                </a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. FEATURES SECTION
    st.markdown('<div id="features"></div>', unsafe_allow_html=True)
    st.markdown("<h3>Core Technological Capabilities</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:14px; margin-top:-8px; margin-bottom:20px;'>Enterprise-grade modular architecture bridging computer vision, robotics telemetry, and deterministic fail-safes.</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon-badge">🎯</div>
            <div class="feature-title">AI-Powered Object Detection</div>
            <div class="feature-desc">
                Ultralytics YOLOv8 inference running locally on companion computers (Jetson/Pi). Identifies humans, vehicles, and hazards with configurable confidence gates.
            </div>
            <div class="feature-status">
                <span>MODEL: YOLOv8 Nano</span>
                <span style="color:#34d399;">INTEGRATED</span>
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon-badge">📹</div>
            <div class="feature-title">Live Video Monitoring</div>
            <div class="feature-desc">
                High-frequency OpenCV optical pipeline equipped with tactical HUD corner-brackets, target center-locking vectors, and dynamic reticle overlays.
            </div>
            <div class="feature-status">
                <span>STREAM: OPENCV LOW-LATENCY</span>
                <span style="color:#34d399;">INTEGRATED</span>
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon-badge">🛡️</div>
            <div class="feature-title">Safety Event Detection</div>
            <div class="feature-desc">
                Automated threat classification logic. If a human presence or flight hazard is detected in the landing corridor, automated emergency RTL or LAND is dispatched.
            </div>
            <div class="feature-status">
                <span>INTERLOCK: USER GUARDED</span>
                <span style="color:#34d399;">ACTIVE</span>
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon-badge">📡</div>
            <div class="feature-title">Drone Telemetry</div>
            <div class="feature-desc">
                Real-time MAVLink packet decoding reading 3D GPS fixes, barometric relative altitude, heading yaw, battery voltage, and armed state flags.
            </div>
            <div class="feature-status">
                <span>PROTOCOL: PYMAVLINK 2.4</span>
                <span style="color:#38bdf8;">SIM / HARDWARE</span>
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon-badge">🕹️</div>
            <div class="feature-title">Mission Monitoring</div>
            <div class="feature-desc">
                Safe command dispatching supporting ArduPilot GUIDED mode. Strictly enforces altitude ceiling caps and requires confirmation before propulsion arming.
            </div>
            <div class="feature-status">
                <span>COMPATIBILITY: ARDUPILOT / PX4</span>
                <span style="color:#38bdf8;">SUPPORTED</span>
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon-badge">📊</div>
            <div class="feature-title">Flight Logs and Analytics</div>
            <div class="feature-desc">
                Continuous in-memory blackbox telemetry recording with chronological event tagging and instant CSV export for mission debriefs and post-flight analysis.
            </div>
            <div class="feature-status">
                <span>EXPORT: RFC-4180 CSV</span>
                <span style="color:#34d399;">INTEGRATED</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5. ARCHITECTURE PIPELINE BREAKDOWN
    st.markdown('<div id="architecture"></div>', unsafe_allow_html=True)
    st.markdown("<h3>System Architecture Pipeline</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class="uas-card" style="margin-bottom: 35px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; font-family: 'Share Tech Mono', monospace; font-size: 13px; text-align: center;">
            <div style="flex: 1; min-width: 120px; padding: 12px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56,189,248,0.2); border-radius: 6px;">
                <span style="font-size: 20px;">📷</span><br><b>CAMERA</b><br><span style="color:#64748b; font-size:11px;">RTSP / USB 0</span>
            </div>
            <span style="color:#38bdf8; font-size: 18px;">➔</span>
            <div style="flex: 1; min-width: 120px; padding: 12px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56,189,248,0.2); border-radius: 6px;">
                <span style="font-size: 20px;">🧠</span><br><b>YOLOv8 AI</b><br><span style="color:#64748b; font-size:11px;">BBox & Class</span>
            </div>
            <span style="color:#38bdf8; font-size: 18px;">➔</span>
            <div style="flex: 1; min-width: 120px; padding: 12px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56,189,248,0.2); border-radius: 6px;">
                <span style="font-size: 20px;">⚖️</span><br><b>DECISION ENGINE</b><br><span style="color:#64748b; font-size:11px;">Threat Eval</span>
            </div>
            <span style="color:#38bdf8; font-size: 18px;">➔</span>
            <div style="flex: 1; min-width: 120px; padding: 12px; background: rgba(20, 184, 166, 0.08); border: 1px solid rgba(20,184,166,0.2); border-radius: 6px;">
                <span style="font-size: 20px;">🛡️</span><br><b>SAFETY GUARD</b><br><span style="color:#64748b; font-size:11px;">Interlock Gate</span>
            </div>
            <span style="color:#38bdf8; font-size: 18px;">➔</span>
            <div style="flex: 1; min-width: 120px; padding: 12px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56,189,248,0.2); border-radius: 6px;">
                <span style="font-size: 20px;">📡</span><br><b>MAVLINK</b><br><span style="color:#64748b; font-size:11px;">PyMAVLink 2.0</span>
            </div>
            <span style="color:#38bdf8; font-size: 18px;">➔</span>
            <div style="flex: 1; min-width: 120px; padding: 12px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56,189,248,0.2); border-radius: 6px;">
                <span style="font-size: 20px;">🛸</span><br><b>FLIGHT CONTROLLER</b><br><span style="color:#64748b; font-size:11px;">ArduPilot / SITL</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 6. FOOTER & CONTACT
    st.markdown('<div id="contact"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="landing-footer">
        <div>
            <div style="font-family: 'Rajdhani', sans-serif; font-size: 18px; font-weight: 700; color: #38bdf8; letter-spacing: 1.5px;">
                AUTONOMOUS DRONE RESEARCH LAB
            </div>
            <div style="color: #64748b; font-size: 13px; margin-top: 4px;">
                Engineered with Python, Ultralytics YOLOv8, OpenCV & PyMAVLink.
            </div>
        </div>
        <div style="font-family: 'Share Tech Mono', monospace; font-size: 12px; text-align: right; color: #94a3b8;">
            <span>STATUS: <b>MISSION READY</b></span><br>
            <span>SECURITY LEVEL: <b>UNCLASSIFIED</b></span><br>
            <span>FIRMWARE: <b>ArduCopter / SITL</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# PAGE 2: OPTICAL SENSOR HUD (CAMERA)
# ==========================================
elif page == "👁️ Optical Sensor HUD":
    st.markdown("<h1>Targeting & Optical Feed</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; margin-top:-8px;'>Live OpenCV camera stream with tactical corner brackets and neural object detection.</p>", unsafe_allow_html=True)
    
    col_video, col_data = st.columns([7, 3])
    
    with col_data:
        st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Optical Sensor Controls</div>", unsafe_allow_html=True)
        start_cam = st.toggle("ACTIVATE CAMERA STREAM")
        
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 15px 0;'>", unsafe_allow_html=True)
        det_count = st.empty()
        st.markdown("</div>", unsafe_allow_html=True)
        
        if start_cam and not st.session_state.detector:
            with st.spinner("Booting Neural Engine (YOLOv8)..."):
                try:
                    st.session_state.detector = ObjectDetector('yolov8n.pt', st.session_state.conf_threshold)
                except Exception as e:
                    st.error(f"FATAL EXCEPTION: {str(e)}")

        if st.session_state.safety.emergency_triggered:
            st.markdown(f'<div class="uas-card" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.1);"><div class="metric-label">CRITICAL THREAT</div><div class="metric-value danger">EMERGENCY PROTOCOL ENGAGED</div></div>', unsafe_allow_html=True)

    with col_video:
        frame_window = st.empty()
        
        if start_cam:
            cap = cv2.VideoCapture(0)
            try:
                if not cap.isOpened():
                    st.error("HARDWARE FAULT: Camera interface unresponsive. Ensure no other application is using the webcam.")
                else:
                    while start_cam:
                        ret, frame = cap.read()
                        if not ret:
                            st.warning("SIGNAL LOST...")
                            time.sleep(0.5)
                            continue
                        
                        # AI Inference
                        if st.session_state.detector:
                            detections = st.session_state.detector.detect(frame)
                            st.session_state.last_detections = detections
                            st.session_state.decision.process_detections(detections)
                            
                            # Military HUD Overlay
                            h, w = frame.shape[:2]
                            
                            # Radar Grid & Crosshair
                            cv2.line(frame, (w//2, 0), (w//2, h), (255, 255, 255), 1, cv2.LINE_4)
                            cv2.line(frame, (0, h//2), (w, h//2), (255, 255, 255), 1, cv2.LINE_4)
                            cv2.circle(frame, (w//2, h//2), 100, (255, 255, 255), 1, cv2.LINE_AA)
                            cv2.circle(frame, (w//2, h//2), 200, (255, 255, 255), 1, cv2.LINE_AA)
                            
                            for det in detections:
                                x1, y1, x2, y2 = det['bbox']
                                l = 20
                                color = (0, 255, 0) if det['class'] != 'person' else (0, 0, 255)
                                t = 2
                                # Tactical Corners
                                cv2.line(frame, (x1, y1), (x1+l, y1), color, t); cv2.line(frame, (x1, y1), (x1, y1+l), color, t)
                                cv2.line(frame, (x2, y1), (x2-l, y1), color, t); cv2.line(frame, (x2, y1), (x2, y1+l), color, t)
                                cv2.line(frame, (x1, y2), (x1+l, y2), color, t); cv2.line(frame, (x1, y2), (x1, y2-l), color, t)
                                cv2.line(frame, (x2, y2), (x2-l, y2), color, t); cv2.line(frame, (x2, y2), (x2, y2-l), color, t)
                                
                                # Tag text
                                cv2.putText(frame, f"TRGT:{det['class'].upper()}", (x1, y1-20), cv2.FONT_HERSHEY_PLAIN, 1.0, color, 1)
                                cv2.putText(frame, f"CNF:{det['confidence']:.2f}", (x1, y1-6), cv2.FONT_HERSHEY_PLAIN, 0.9, color, 1)
                                
                                # Lock line to center
                                cv2.line(frame, (w//2, h//2), ((x1+x2)//2, (y1+y2)//2), color, 1)
                        else:
                            detections = []
                        
                        timestamp = datetime.now().strftime("T+%H:%M:%S.%f")[:-4]
                        cv2.putText(frame, f"REC // {timestamp}", (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)

                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_window.image(frame, channels="RGB", use_container_width=True)
                        
                        det_count.markdown(f'<div class="metric-label">LOCKED TARGETS</div><div class="metric-value {"danger" if len(detections)>0 else "safe"}">{len(detections)}</div>', unsafe_allow_html=True)
                        time.sleep(0.04)
            finally:
                cap.release()
        else:
            frame_window.markdown("""
            <div style="height: 450px; background-color: #050810; border: 1px solid rgba(56,189,248,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <h3 style="color: #334155; font-family: 'Share Tech Mono', monospace; letter-spacing: 4px;">OPTICAL SENSOR OFFLINE</h3>
                <p style="color: #1e293b; font-family: 'Share Tech Mono', monospace;">TOGGLE 'ACTIVATE CAMERA STREAM' TO INITIALIZE</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# PAGE 3: FLIGHT OPERATIONS & TELEMETRY
# ==========================================
elif page == "🎮 Flight Ops & Telemetry":
    st.markdown("<h1>Flight Operations & Telemetry</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; margin-top:-8px;'>MAVLink bi-directional uplink, guarded flight commands, and live navigation telemetry.</p>", unsafe_allow_html=True)
    
    col_cmd, col_tel = st.columns([3, 7])
    
    with col_cmd:
        st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
        st.markdown("<span class='metric-label' style='color:#0ea5e9;'>COMMUNICATION LINK</span><br>", unsafe_allow_html=True)
        
        if not st.session_state.is_connected:
            if st.button("INITIALIZE MAVLINK"):
                with st.spinner("Establishing secure handshake..."):
                    conn = MavlinkConnection(Config.CONNECTION_STRING, Config.BAUD_RATE)
                    if conn.connect(timeout=5):
                        st.session_state.conn = conn
                        st.session_state.is_connected = True
                        st.session_state.telemetry = Telemetry(conn)
                        st.session_state.safety = SafetyManager(conn)
                        st.session_state.decision.safety = st.session_state.safety
                        st.rerun()
                    else:
                        st.error("UPLINK FAILED. Ensure SITL or flight controller is active.")
        else:
            if st.button("TERMINATE LINK"):
                st.session_state.conn.close()
                st.session_state.is_connected = False
                st.rerun()
                
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 20px 0;'>", unsafe_allow_html=True)
        st.markdown("<span class='metric-label' style='color:#0ea5e9;'>FLIGHT COMMANDS</span><br>", unsafe_allow_html=True)
        confirm = st.checkbox("DEACTIVATE SAFETY INTERLOCK")
        
        st.button("ARM PROPULSION", disabled=not (confirm and st.session_state.is_connected), on_click=lambda: st.session_state.safety.request_arm(ui_confirmed=True))
        st.button("TAKEOFF [5M]", disabled=not (confirm and st.session_state.is_connected), on_click=lambda: st.session_state.safety.request_takeoff(altitude=5.0, ui_confirmed=True))
        st.button("AUTO-LAND", disabled=not st.session_state.is_connected, on_click=lambda: st.session_state.safety.commander.land())
        st.button("RTL BASE", disabled=not st.session_state.is_connected, on_click=lambda: st.session_state.safety.commander.return_to_launch())
        st.markdown("</div>", unsafe_allow_html=True)

    with col_tel:
        st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
        
        if st.session_state.is_connected:
            status = st.session_state.telemetry.get_status()
            pos = st.session_state.telemetry.get_position()
            batt = st.session_state.telemetry.get_battery()
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="metric-label">SYSTEM STATE</div><div class="metric-value {"danger" if status.get("armed") else "safe"}">{"ARMED" if status.get("armed") else "DISARMED"}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-label">NAV MODE</div><div class="metric-value">{status.get("mode", "UNK")}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-label">ALTITUDE (Z)</div><div class="metric-value safe">{pos.get("alt", 0):.2f} m</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-label">YAW (HEADING)</div><div class="metric-value">{pos.get("heading", 0):.1f}°</div>', unsafe_allow_html=True)
            with c3:
                batt_rem = batt.get('remaining', 0)
                st.markdown(f'<div class="metric-label">MAIN BATTERY</div><div class="metric-value {"safe" if batt_rem > 20 else "danger"}">{batt_rem}%</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-label">BUS VOLTAGE</div><div class="metric-value">{batt.get("voltage", 0):.2f} V</div>', unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; color: #334155; font-family: \"Share Tech Mono\"; margin: 40px 0;'><h2 style='color: #334155;'>TELEMETRY OFFLINE</h2><p>MAVLINK PROTOCOL DISCONNECTED. CONNECT UPLINK TO RETRIEVE TELEMETRY.</p></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# PAGE 4: BLACKBOX LOGS
# ==========================================
elif page == "📋 Blackbox Logs":
    st.markdown("<h1>Encrypted Blackbox Logs</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; margin-top:-8px;'>Chronological flight recorder records and CSV export utility.</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='uas-card'>", unsafe_allow_html=True)
    logs = flight_logger.get_logs_df()
    if not logs.empty:
        st.dataframe(logs.tail(100), use_container_width=True)
        csv = logs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DECRYPT & EXPORT LOGS (CSV)", csv, "blackbox_export.csv", "text/csv")
    else:
        st.info("NO SYSTEM EVENTS RECORDED YET.")
    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# PAGE 5: MISSION DIAGNOSTICS
# ==========================================
elif page == "⚙️ Mission Diagnostics":
    st.markdown("<h1>Mission Diagnostics & Parameters</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="uas-card">
            <div class="metric-label">Sub-System Verification</div>
            <table style="width: 100%; text-align: left; font-family: 'Share Tech Mono'; font-size: 14px; margin-top: 15px;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);"><td style="padding: 12px 0;">MAVLINK_COMM</td><td style="text-align: right;">{draw_badge("PASS", "ok") if st.session_state.is_connected else draw_badge("OFFLINE", "error")}</td></tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);"><td style="padding: 12px 0;">YOLOv8_ENGINE</td><td style="text-align: right;">{draw_badge("ACTIVE", "ok") if st.session_state.detector else draw_badge("STANDBY", "warn")}</td></tr>
                <tr><td style="padding: 12px 0;">SAFETY_INTERLOCK</td><td style="text-align: right;">{draw_badge("ENABLED", "ok") if Config.REQUIRE_CONFIRMATION else draw_badge("DISABLED", "warn")}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="uas-card">
            <div class="metric-label">Parameter Configuration</div>
            <div style="font-family: 'Share Tech Mono'; color: #94a3b8; font-size: 13px; line-height: 1.8; margin-top: 15px;">
                CONNECTION_STRING: <span style="color:#38bdf8;">{Config.CONNECTION_STRING}</span> <br>
                BAUD_RATE: <span style="color:#e2e8f0;">{Config.BAUD_RATE}</span> <br>
                MAX_CEILING_ALT: <span style="color:#e2e8f0;">{Config.MAX_ALTITUDE}m</span> <br>
                SAFETY_CONFIRMATION: <span style="color:#34d399;">{'ENABLED' if Config.REQUIRE_CONFIRMATION else 'DISABLED'}</span> <br>
                CONFIDENCE_THRESHOLD: <span style="color:#e2e8f0;">{st.session_state.conf_threshold * 100}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
