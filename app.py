import os
import time
import tempfile
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from datetime import datetime

# Import modular components
from detector import ObstacleDetector
from landing import LandingZoneAnalyzer
import utils

# Set page configuration
st.set_page_config(
    page_title="SafeLand AI - Drone Landing Detection",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom dark-theme CSS injection for a premium dashboard feel
st.markdown(
    """
    <style>
    /* Main container background */
    .stApp {
        background-color: #0b0c10;
        color: #c5c6c7;
    }
    
    /* Headers styling */
    h1, h2, h3 {
        color: #66fcf1 !important;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metrics glassmorphism cards */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 25px;
    }
    .metric-card {
        background: rgba(31, 40, 51, 0.4);
        border: 1px solid rgba(102, 252, 241, 0.2);
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(102, 252, 241, 0.5);
    }
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #85929E;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
    }
    .status-safe {
        color: #00ff88 !important;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    }
    .status-caution {
        color: #ffaa00 !important;
        text-shadow: 0 0 10px rgba(255, 170, 0, 0.3);
    }
    .status-unsafe {
        color: #ff4444 !important;
        text-shadow: 0 0 10px rgba(255, 68, 68, 0.3);
    }
    
    /* Streamlit overrides */
    .stSidebar {
        background-color: #1f2833 !important;
        border-right: 1px solid rgba(102, 252, 241, 0.1);
    }
    .stButton>button {
        background-color: #45f3ff !important;
        color: #0b0c10 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 252, 241, 0.2) !important;
    }
    .stButton>button:hover {
        background-color: #66fcf1 !important;
        transform: scale(1.02) !important;
        box-shadow: 0 4px 20px rgba(102, 252, 241, 0.4) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize output folders
outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(outputs_dir, exist_ok=True)

# Application Header
st.title("🛸 SAFELAND AI")
st.subheader("Autonomous Drone Landing Zone Detection System")
st.write("Using YOLOv8 obstacle detection & computerized terrain mapping to identify safe landing zones.")

# Sidebar Configuration Controls
st.sidebar.header("⚙️ System Configuration")

mode = st.sidebar.selectbox(
    "Select Input Source",
    ["Upload Video", "Webcam Feed / Camera", "Static Image Calibration"]
)

conf_threshold = st.sidebar.slider(
    "YOLOv8 Confidence Threshold",
    min_value=0.1,
    max_value=1.0,
    value=0.4,
    step=0.05,
    help="Minimum confidence to detect an object as an obstacle."
)

grid_size = st.sidebar.slider(
    "Terrain Grid Divisions",
    min_value=4,
    max_value=16,
    value=8,
    step=2,
    help="Subdivides the field of view into an NxN grid of candidates."
)

min_safe_score = st.sidebar.slider(
    "Minimum Safety Score threshold",
    min_value=30,
    max_value=80,
    value=50,
    step=5,
    help="Minimum score needed for a zone to be highlighted in Green."
)

# Initialize Detector and Analyzer with cache/session state to speed up reload
if "detector" not in st.session_state or st.session_state.get("prev_conf") != conf_threshold:
    st.session_state.detector = ObstacleDetector(confidence_threshold=conf_threshold)
    st.session_state.prev_conf = conf_threshold

detector = st.session_state.detector
analyzer = LandingZoneAnalyzer(grid_size=grid_size, min_safe_score=min_safe_score)

# Helper function to render glassmorphism metric cards
def render_metric_cards(score, status, coords_str, obstacle_count):
    status_class = "status-safe"
    if status == "CAUTION":
        status_class = "status-caution"
    elif status == "UNSAFE":
        status_class = "status-unsafe"

    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-title">Landing Safety Score</div>
                <div class="metric-value {status_class}">{score}/100</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Deployment Status</div>
                <div class="metric-value {status_class}">{status}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Optimal Coordinates</div>
                <div class="metric-value" style="font-size: 1.5rem; line-height: 2.2rem; color: #66fcf1;">{coords_str}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Active Obstacles</div>
                <div class="metric-value" style="color: #ff4444;">{obstacle_count}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------- MODE: STATIC IMAGE -----------------
if mode == "Static Image Calibration":
    st.write("### 🖼️ Static Image Terrain Calibration")
    uploaded_image = st.file_uploader("Upload a drone aerial view image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_image is not None:
        # Load image
        img = Image.open(uploaded_image)
        img_np = np.array(img)
        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        with st.spinner("Analyzing terrain features..."):
            start_time = time.time()
            detections = detector.detect(img_bgr)
            best_zone, zones = analyzer.analyze(img_bgr, detections)
            fps = 1.0 / (time.time() - start_time)
            
            # Draw overlays on a copy of the image
            display_img = img_bgr.copy()
            utils.draw_zones(display_img, zones, min_safe_score=min_safe_score)
            utils.draw_detections(display_img, detections)
            utils.draw_landing_target(display_img, best_zone)
            utils.draw_hud(display_img, best_zone["score"] if best_zone else 0, fps, best_zone, min_safe_score)
            
            # Show Metrics
            score = best_zone["score"] if best_zone else 0
            status = "SAFE" if score >= min_safe_score else ("CAUTION" if score > 20 else "UNSAFE")
            coords_str = f"X: {best_zone['center'][0]} px<br>Y: {best_zone['center'][1]} px" if best_zone else "N/A"
            render_metric_cards(score, status, coords_str, len(detections))
            
            # Display image
            st.image(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB), caption="Processed Calibration Frame", use_container_width=True)
            
            # Detailed diagnostics details
            col1, col2 = st.columns(2)
            with col1:
                st.write("#### 🛡️ Obstacle Detection List")
                if len(detections) > 0:
                    obstacle_table = []
                    for idx, det in enumerate(detections):
                        obstacle_table.append({
                            "Index": idx + 1,
                            "Obstacle": det["friendly_name"],
                            "Risk Class": det["category"],
                            "Confidence": f"{det['confidence'] * 100:.1f}%",
                            "Bounding Box": str(det["bbox"])
                        })
                    st.table(obstacle_table)
                else:
                    st.success("No critical obstacles detected in this frame.")
                    
            with col2:
                st.write("#### 📊 Terrain Characteristics")
                avg_edge = np.mean([z["edge_ratio"] for z in zones]) * 100
                avg_green = np.mean([z["green_ratio"] for z in zones]) * 100
                avg_water = np.mean([z["water_ratio"] for z in zones]) * 100
                
                st.info(f"🌿 Average Vegetation Density: **{avg_green:.1f}%**")
                st.info(f"🌊 Average Water Surface Coverage: **{avg_water:.1f}%**")
                st.info(f"⛰️ Average Surface Edge Complexity (Edges): **{avg_edge:.1f}%**")
            
            # Generate Report PDF
            report_data = {
                "overall_score": score,
                "status": status,
                "best_point": best_zone["center"] if best_zone else None,
                "best_zone_id": best_zone["id"] if best_zone else "N/A",
                "edge_density": float(np.mean([z["edge_ratio"] for z in zones])),
                "green_ratio": float(np.mean([z["green_ratio"] for z in zones])),
                "water_ratio": float(np.mean([z["water_ratio"] for z in zones])),
                "obstacles": detections
            }
            
            pdf_path = os.path.join(outputs_dir, "calibration_report.pdf")
            utils.generate_pdf_report(report_data, pdf_path)
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 Download Calibration Report PDF",
                    data=f,
                    file_name="calibration_report.pdf",
                    mime="application/pdf"
                )

# ----------------- MODE: VIDEO UPLOAD -----------------
elif mode == "Upload Video":
    st.write("### 📹 Drone Video Landing Spot Search")
    uploaded_video = st.file_uploader("Upload a drone flight video...", type=["mp4", "avi", "mov", "mkv"])
    
    if uploaded_video is not None:
        # Save uploaded file to temp file
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())
        tfile.close()
        
        video_cap = cv2.VideoCapture(tfile.name)
        
        width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_in = video_cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        st.write(f"**Video details:** {width}x{height} | {fps_in:.1f} FPS | {frame_count} total frames")
        
        # Setup output writer
        out_video_path = os.path.join(outputs_dir, "processed_landing_run.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec for writing processed video
        out_writer = cv2.VideoWriter(out_video_path, fourcc, fps_in, (width, height))
        
        # Placeholders for Streamlit display
        st.write("#### ⚡ Live Video Processing telemetry")
        frame_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        # Stats tracking throughout the run
        scores_history = []
        unique_obstacles = {}
        best_overall_zone = None
        best_overall_score = -1
        
        # Diagnostics placeholders
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            stats_placeholder = st.empty()
        with info_col2:
            warning_placeholder = st.empty()
            
        start_process_time = time.time()
        frame_idx = 0
        
        while video_cap.isOpened():
            ret, frame = video_cap.read()
            if not ret:
                break
                
            frame_start = time.time()
            
            # Detect & Analyze
            detections = detector.detect(frame)
            best_zone, zones = analyzer.analyze(frame, detections)
            
            # Track statistics
            current_score = best_zone["score"] if best_zone else 0
            scores_history.append(current_score)
            
            # Save the highest scoring landing zone across the entire flight
            if current_score > best_overall_score:
                best_overall_score = current_score
                best_overall_zone = best_zone
                
            for det in detections:
                unique_obstacles[det["friendly_name"]] = det
                
            # FPS calculation
            frame_end = time.time()
            fps = 1.0 / (frame_end - frame_start) if (frame_end - frame_start) > 0 else fps_in
            
            # Draw overlays
            processed_frame = frame.copy()
            utils.draw_zones(processed_frame, zones, min_safe_score=min_safe_score)
            utils.draw_detections(processed_frame, detections)
            utils.draw_landing_target(processed_frame, best_zone)
            utils.draw_hud(processed_frame, current_score, fps, best_zone, min_safe_score)
            
            # Write to output file
            out_writer.write(processed_frame)
            
            # Display current frame (convert BGR to RGB)
            frame_placeholder.image(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
            
            # Update metrics panels
            status = "SAFE" if current_score >= min_safe_score else ("CAUTION" if current_score > 20 else "UNSAFE")
            coords_str = f"X: {best_zone['center'][0]} px<br>Y: {best_zone['center'][1]} px" if best_zone else "N/A"
            
            with stats_placeholder.container():
                st.write("**Instant Telemetry:**")
                st.write(f"- Frame: **{frame_idx+1}/{frame_count}**")
                st.write(f"- Current Frame Safety Score: **{current_score}/100**")
                st.write(f"- Optimal coordinates: **X={best_zone['center'][0]}, Y={best_zone['center'][1]}**" if best_zone else "Coordinates: N/A")
                st.write(f"- FPS: **{fps:.1f}**")
                
            if current_score < min_safe_score:
                warning_placeholder.warning(f"⚠️ **Alert Frame {frame_idx+1}:** Landing safety score below threshold. Unstable ground or obstacle threat detected!")
            else:
                warning_placeholder.success("✅ **Telemetry Clear:** Stable landing point identified.")
                
            frame_idx += 1
            progress_bar.progress(min(1.0, frame_idx / frame_count))
            
        video_cap.release()
        out_writer.release()
        
        # Final Summary Panel
        st.write("---")
        st.success(f"🎉 Processing complete! Total time: {time.time() - start_process_time:.1f}s")
        
        # Display Best LZ found during the video
        st.write("### 🏆 Optimal Landing Target Found During Flight")
        final_score = int(np.mean(scores_history)) if scores_history else 0
        final_status = "SAFE" if best_overall_score >= min_safe_score else ("CAUTION" if best_overall_score > 20 else "UNSAFE")
        final_coords = f"X: {best_overall_zone['center'][0]} px<br>Y: {best_overall_zone['center'][1]} px" if best_overall_zone else "N/A"
        
        render_metric_cards(best_overall_score, final_status, final_coords, len(unique_obstacles))
        
        # Download buttons section
        down_col1, down_col2 = st.columns(2)
        
        # 1. Download Processed Video
        with down_col1:
            st.write("#### 🎥 Export Processed Flight Video")
            with open(out_video_path, "rb") as f:
                st.download_button(
                    label="📥 Download Annotated Video File",
                    data=f,
                    file_name="safeland_annotated_run.mp4",
                    mime="video/mp4"
                )
                
        # 2. PDF Report download
        with down_col2:
            st.write("#### 📄 Flight Safety Assessment Report")
            report_data = {
                "overall_score": best_overall_score,
                "status": final_status,
                "best_point": best_overall_zone["center"] if best_overall_zone else None,
                "best_zone_id": best_overall_zone["id"] if best_overall_zone else "N/A",
                "edge_density": 0.05,  # Estimate or store frame average
                "green_ratio": 0.50,
                "water_ratio": 0.0,
                "obstacles": list(unique_obstacles.values())
            }
            pdf_path = os.path.join(outputs_dir, "flight_landing_report.pdf")
            utils.generate_pdf_report(report_data, pdf_path)
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 Download Flight Landing Report PDF",
                    data=f,
                    file_name="flight_landing_report.pdf",
                    mime="application/pdf"
                )

# ----------------- MODE: WEBCAM FEED -----------------
elif mode == "Webcam Feed / Camera":
    st.write("### 📷 Live Camera Feed Landing Analysis")
    st.write("Aim your camera at flat terrains, grass, pavement, or simulate aerial objects to test obstacle avoidances in real-time.")
    
    # Toggle to start/stop webcam loop
    run_webcam = st.toggle("Start Live Telemetry Feed", value=False)
    
    if run_webcam:
        webcam_cap = cv2.VideoCapture(0)
        
        # Webcams don't always support custom resolutions instantly, check properties
        w = int(webcam_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(webcam_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        webcam_frame_placeholder = st.empty()
        
        # Stats columns
        webcam_stat1, webcam_stat2 = st.columns(2)
        with webcam_stat1:
            webcam_metrics_placeholder = st.empty()
        with webcam_stat2:
            webcam_warning_placeholder = st.empty()
            
        # Add a screenshot/snapshot flag to generate reports
        capture_report = st.button("Capture Snapshot & Generate PDF Report")
        
        prev_time = time.time()
        
        while run_webcam:
            ret, frame = webcam_cap.read()
            if not ret:
                st.error("Unable to access the system camera/webcam feed.")
                break
                
            frame_start = time.time()
            
            # Detect and Analyze
            detections = detector.detect(frame)
            best_zone, zones = analyzer.analyze(frame, detections)
            
            # FPS Calculation
            frame_end = time.time()
            fps = 1.0 / (frame_end - frame_start) if (frame_end - frame_start) > 0 else 30.0
            
            current_score = best_zone["score"] if best_zone else 0
            
            # Draw overlays
            annotated_frame = frame.copy()
            utils.draw_zones(annotated_frame, zones, min_safe_score=min_safe_score)
            utils.draw_detections(annotated_frame, detections)
            utils.draw_landing_target(annotated_frame, best_zone)
            utils.draw_hud(annotated_frame, current_score, fps, best_zone, min_safe_score)
            
            # Stream to Streamlit dashboard
            webcam_frame_placeholder.image(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
            
            # Display real-time stats
            status = "SAFE" if current_score >= min_safe_score else ("CAUTION" if current_score > 20 else "UNSAFE")
            
            with webcam_metrics_placeholder.container():
                st.write("#### 📊 Live Coordinates & Score")
                st.write(f"- Landing Score: **{current_score}/100**")
                st.write(f"- Safety Evaluation: **{status}**")
                st.write(f"- Target Coordinates: **X={best_zone['center'][0] if best_zone else 'N/A'}, Y={best_zone['center'][1] if best_zone else 'N/A'}**")
                st.write(f"- Real-time FPS: **{fps:.1f}**")
                
            with webcam_warning_placeholder.container():
                if current_score < min_safe_score:
                    st.warning("⚠️ **Landing Threat Detected:** Land site is currently blocked or too complex. Hold hover position.")
                else:
                    st.success("✅ **Landing Zone Verified:** Autonomous landing clearance granted.")
            
            # Check for report capture command
            if capture_report:
                snap_path = os.path.join(outputs_dir, "webcam_snapshot.jpg")
                cv2.imwrite(snap_path, annotated_frame)
                
                # Assemble PDF
                report_data = {
                    "overall_score": current_score,
                    "status": status,
                    "best_point": best_zone["center"] if best_zone else None,
                    "best_zone_id": best_zone["id"] if best_zone else "N/A",
                    "edge_density": float(np.mean([z["edge_ratio"] for z in zones])),
                    "green_ratio": float(np.mean([z["green_ratio"] for z in zones])),
                    "water_ratio": float(np.mean([z["water_ratio"] for z in zones])),
                    "obstacles": detections
                }
                pdf_path = os.path.join(outputs_dir, "live_snapshot_report.pdf")
                utils.generate_pdf_report(report_data, pdf_path)
                
                st.success("📝 Snapshot Report generated successfully! You can download it below.")
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Snapshot Report PDF",
                        data=f,
                        file_name="safeland_snapshot_report.pdf",
                        mime="application/pdf"
                    )
                capture_report = False # Reset flag
                
            time.sleep(0.01) # Avoid tight loop CPU overloading
            
        webcam_cap.release()
