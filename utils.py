import os
import cv2
import numpy as np
from datetime import datetime
from fpdf import FPDF

# Color Definitions (BGR for OpenCV)
COLOR_SAFE = (0, 255, 136)      # Neon Green
COLOR_CAUTION = (0, 170, 255)   # Amber/Orange
COLOR_UNSAFE = (0, 0, 255)      # Red
COLOR_HUD_BG = (20, 20, 20)     # Very Dark Gray
COLOR_TEXT = (255, 255, 255)    # White

def draw_zones(frame, zones, min_safe_score=50):
    """
    Draws the landing grid overlay on the frame.
    Green = Safe, Yellow/Orange = Caution, Red = Unsafe.
    """
    h, w, _ = frame.shape
    overlay = frame.copy()

    for zone in zones:
        x1, y1, x2, y2 = zone["bbox"]
        score = zone["score"]

        # Determine color and transparency based on safety score
        if score >= min_safe_score:
            # Scale alpha based on safety score (safer = slightly more visible green)
            color = COLOR_SAFE
            alpha = 0.25
        elif score > 20:
            color = COLOR_CAUTION
            alpha = 0.3
        else:
            color = COLOR_UNSAFE
            alpha = 0.35

        # Draw filled zone on overlay
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        # Draw border
        cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 50, 50), 1)

        # Draw safety score text in the center of the cell
        cx, cy = zone["center"]
        cv2.putText(frame, str(score), (cx - 10, cy + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_TEXT, 1, cv2.LINE_AA)

    # Apply transparency overlay
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

def draw_detections(frame, detections):
    """
    Draws bounding boxes and labels for the detected obstacles.
    """
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = det["friendly_name"]
        conf = det["confidence"]
        category = det["category"]

        color = COLOR_UNSAFE if category == "DANGEROUS" else COLOR_CAUTION

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Draw text background banner
        text_str = f"{label} {conf:.2f}"
        (text_w, text_h), baseline = cv2.getTextSize(text_str, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.rectangle(frame, (x1, y1 - text_h - 6), (x1 + text_w + 6, y1), color, -1)

        # Draw text label
        cv2.putText(frame, text_str, (x1 + 3, y1 - 4), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0) if color == COLOR_CAUTION else COLOR_TEXT, 1, cv2.LINE_AA)

def draw_landing_target(frame, best_zone):
    """
    Draws a glowing tactical crosshair/landing target over the best landing zone center.
    """
    if not best_zone:
        return

    cx, cy = best_zone["center"]
    
    # Outer ring
    cv2.circle(frame, (cx, cy), 25, COLOR_SAFE, 2, cv2.LINE_AA)
    # Inner ring
    cv2.circle(frame, (cx, cy), 12, COLOR_SAFE, 1, cv2.LINE_AA)
    # Center dot
    cv2.circle(frame, (cx, cy), 3, COLOR_SAFE, -1, cv2.LINE_AA)
    
    # Crosshair lines
    cv2.line(frame, (cx - 35, cy), (cx - 15, cy), COLOR_SAFE, 2, cv2.LINE_AA)
    cv2.line(frame, (cx + 15, cy), (cx + 35, cy), COLOR_SAFE, 2, cv2.LINE_AA)
    cv2.line(frame, (cx, cy - 35), (cx, cy - 15), COLOR_SAFE, 2, cv2.LINE_AA)
    cv2.line(frame, (cx, cy + 15), (cx, cy + 35), COLOR_SAFE, 2, cv2.LINE_AA)
    
    # Draw "BEST L.Z." label
    cv2.putText(frame, "BEST LZ", (cx - 28, cy - 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_SAFE, 1, cv2.LINE_AA)

def draw_hud(frame, overall_score, fps, best_zone, min_safe_score=50):
    """
    Draws a modern telemetry HUD on top of the frame.
    """
    h, w, _ = frame.shape
    
    # Top HUD Banner Background
    hud_h = 60
    hud_overlay = frame.copy()
    cv2.rectangle(hud_overlay, (0, 0), (w, hud_h), COLOR_HUD_BG, -1)
    cv2.addWeighted(hud_overlay, 0.7, frame, 0.3, 0, frame)
    
    # Border line for HUD
    cv2.line(frame, (0, hud_h), (w, hud_h), (50, 50, 50), 1)

    # 1. Title / Project Name
    cv2.putText(frame, "SAFELAND AI - TELEMETRY", (15, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXT, 2, cv2.LINE_AA)
    
    # 2. Overall Status / Score
    status = "SAFE TO LAND" if overall_score >= min_safe_score else "UNSAFE ZONE"
    status_color = COLOR_SAFE if overall_score >= min_safe_score else COLOR_UNSAFE
    
    cv2.putText(frame, f"STATUS: {status}", (15, 45), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1, cv2.LINE_AA)

    # 3. Best LZ coordinates & Safety Score (Right aligned)
    score_str = f"SAFETY SCORE: {overall_score}/100"
    cv2.putText(frame, score_str, (w - 220, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2, cv2.LINE_AA)

    if best_zone:
        cx, cy = best_zone["center"]
        coord_str = f"TARGET COORDS: X={cx}, Y={cy}"
        cv2.putText(frame, coord_str, (w - 220, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_TEXT, 1, cv2.LINE_AA)
    else:
        cv2.putText(frame, "TARGET COORDS: N/A", (w - 220, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_UNSAFE, 1, cv2.LINE_AA)

    # 4. FPS Indicator (Top Center)
    fps_str = f"FPS: {fps:.1f}"
    cv2.putText(frame, fps_str, (w // 2 - 30, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_CAUTION, 1, cv2.LINE_AA)

class PDFReportGenerator(FPDF):
    def header(self):
        # Draw a beautiful dark header banner
        self.set_fill_color(30, 30, 30)
        self.rect(0, 0, 210, 35, 'F')
        
        # Logo text
        self.set_text_color(0, 255, 136) # SafeLand green
        self.set_font('helvetica', 'B', 20)
        self.text(15, 22, "SAFELAND AI")
        
        # Sub-title
        self.set_text_color(200, 200, 200)
        self.set_font('helvetica', '', 10)
        self.text(15, 29, "Autonomous Drone Landing Zone Detection Report")
        
        # Date & Time (Top Right)
        self.set_text_color(150, 150, 150)
        self.set_font('helvetica', '', 9)
        self.text(140, 20, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.ln(30)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(data, output_path):
    """
    Generates a beautifully structured PDF landing analysis report.
    """
    pdf = PDFReportGenerator()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- SECTION 1: EXECUTIVE SUMMARY ---
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, "1. Landing Zone Safety Summary", ln=True)
    pdf.line(10, 45, 200, 45)
    pdf.ln(3)

    # Metrics Layout (2 column table style)
    overall_score = data["overall_score"]
    status = data["status"]
    best_point = data["best_point"]
    best_zone_id = data["best_zone_id"]

    pdf.set_font("helvetica", "", 11)
    
    # Status Alert Banner
    if status == "SAFE":
        pdf.set_fill_color(220, 255, 230) # Light Green
        pdf.set_text_color(0, 100, 40)
        status_text = "STATUS: SAFE TO LAND"
    elif status == "CAUTION":
        pdf.set_fill_color(255, 243, 210) # Light Yellow
        pdf.set_text_color(150, 80, 0)
        status_text = "STATUS: CAUTION ADVISED"
    else:
        pdf.set_fill_color(255, 220, 220) # Light Red
        pdf.set_text_color(150, 0, 0)
        status_text = "STATUS: UNSAFE / NO LANDING RECOMMENDED"

    pdf.cell(0, 8, status_text, ln=True, fill=True, align='C')
    pdf.ln(5)

    # Metric Cards
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(90, 8, "Overall Safety Score:", border=0)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(100, 8, f"{overall_score} / 100", border=0, ln=True)

    pdf.set_font("helvetica", "B", 10)
    pdf.cell(90, 8, "Best Landing Point Coordinates (Center):", border=0)
    pdf.set_font("helvetica", "", 10)
    if best_point:
        pdf.cell(100, 8, f"X={best_point[0]}, Y={best_point[1]} (Grid: {best_zone_id})", border=0, ln=True)
    else:
        pdf.cell(100, 8, "N/A (No suitable landing point)", border=0, ln=True)

    pdf.ln(5)

    # --- SECTION 2: TERRAIN ANALYSIS DETAILS ---
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "2. Terrain Analysis Diagnostics", ln=True)
    pdf.line(10, 93, 200, 93)
    pdf.ln(3)

    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 8, f"Average Edge Density:", border=0)
    pdf.cell(100, 8, f"{data['edge_density'] * 100:.2f}% (Higher indicates rough/complex terrain)", border=0, ln=True)

    pdf.cell(90, 8, f"Green Vegetation Ratio:", border=0)
    pdf.cell(100, 8, f"{data['green_ratio'] * 100:.2f}%", border=0, ln=True)

    pdf.cell(90, 8, f"Water Body Coverage:", border=0)
    pdf.cell(100, 8, f"{data['water_ratio'] * 100:.2f}% (Water is classified as immediate obstacle)", border=0, ln=True)

    pdf.ln(5)

    # --- SECTION 3: DETECTED OBSTACLES ---
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "3. Detected Obstacles Log", ln=True)
    pdf.line(10, 140, 200, 140)
    pdf.ln(3)

    # Table Header
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 8, "Obstacle Type", border=1, fill=True)
    pdf.cell(40, 8, "Confidence", border=1, fill=True)
    pdf.cell(45, 8, "Risk Severity", border=1, fill=True)
    pdf.cell(45, 8, "Location (Grid Zone)", border=1, fill=True, ln=True)

    pdf.set_font("helvetica", "", 9)
    obstacles = data.get("obstacles", [])
    
    if len(obstacles) == 0:
        pdf.cell(190, 8, "No obstacles detected in the landing zone area.", border=1, align="C", ln=True)
    else:
        for idx, obs in enumerate(obstacles):
            # Alternate row background
            fill = idx % 2 == 1
            pdf.set_fill_color(250, 250, 250)
            
            pdf.cell(60, 8, obs["friendly_name"], border=1, fill=fill)
            pdf.cell(40, 8, f"{obs['confidence'] * 100:.1f}%", border=1, fill=fill)
            
            # Text color for severity
            if obs["category"] == "DANGEROUS":
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(180, 100, 0)
                
            pdf.cell(45, 8, obs["category"], border=1, fill=fill)
            pdf.set_text_color(50, 50, 50) # reset
            
            # Simple grid mapping if possible, otherwise coordinates
            loc_str = f"Center X={obs['center'][0]}, Y={obs['center'][1]}" if "center" in obs else "Detected"
            pdf.cell(45, 8, loc_str, border=1, fill=fill, ln=True)

    pdf.ln(10)
    
    # --- FOOTNOTE / DISCLAIMER ---
    pdf.set_font("helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    disclaimer = ("Disclaimer: SafeLand AI is an autonomous assistance dashboard using machine learning "
                  "predictions. Real-world drone deployment requires manual verification, physical sensor "
                  "telemetry (LiDAR, ultrasonic sensors), and compliance with local aviation regulatory authorities.")
    pdf.multi_cell(0, 4, disclaimer, border=0)

    # Save PDF
    pdf.output(output_path)
    print(f"Report generated and saved to {output_path}")
