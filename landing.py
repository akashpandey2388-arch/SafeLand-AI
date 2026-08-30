import cv2
import numpy as np

class LandingZoneAnalyzer:
    def __init__(self, grid_size=8, min_safe_score=50):
        """
        Initializes the landing zone analyzer.
        :param grid_size: Number of subdivisions along each axis (e.g. 8 for 8x8 grid).
        :param min_safe_score: Minimum safety score required to consider a zone safe.
        """
        self.grid_size = grid_size
        self.min_safe_score = min_safe_score

    def analyze(self, frame, detections):
        """
        Analyzes the frame and returns grid zone scores and the best landing point.
        
        :param frame: OpenCv BGR image.
        :param detections: List of dicts representing detections from ObstacleDetector.
        :returns: A tuple of (best_zone_info, list_of_all_zones)
        """
        if frame is None:
            return None, []

        h, w, _ = frame.shape
        cell_h = h // self.grid_size
        cell_w = w // self.grid_size

        # Precompute edge detection for the entire frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Precompute HSV image for color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        zones = []
        best_score = -1
        best_zone = None

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                # Calculate cell pixel bounds
                x1 = col * cell_w
                y1 = row * cell_h
                x2 = w if col == self.grid_size - 1 else (col + 1) * cell_w
                y2 = h if row == self.grid_size - 1 else (row + 1) * cell_h

                cell_area = (x2 - x1) * (y2 - y1)
                
                # Extract sub-regions
                cell_gray = gray[y1:y2, x1:x2]
                cell_edges = edges[y1:y2, x1:x2]
                cell_hsv = hsv[y1:y2, x1:x2]

                # 1. Edge density analysis (0 to 100 penalty)
                edge_count = np.sum(cell_edges > 0)
                edge_ratio = edge_count / cell_area
                edge_penalty = min(80, edge_ratio * 400)  # scale penalty

                # 2. Texture variance analysis (standard deviation)
                std_dev = np.std(cell_gray)
                # Lower standard deviation indicates flat surfaces (like pavement or grass)
                # Higher standard deviation indicates rough terrain, trees, rocks
                texture_penalty = min(50, max(0, (std_dev - 10) * 1.5))

                # 3. Color analysis (detect water and vegetation)
                # Water (Blue range)
                lower_blue = np.array([90, 50, 30])
                upper_blue = np.array([130, 255, 255])
                blue_mask = cv2.inRange(cell_hsv, lower_blue, upper_blue)
                water_ratio = np.sum(blue_mask > 0) / cell_area
                water_penalty = 100 if water_ratio > 0.05 else (water_ratio * 1000)

                # Grass/Vegetation (Green range)
                lower_green = np.array([35, 40, 40])
                upper_green = np.array([85, 255, 255])
                green_mask = cv2.inRange(cell_hsv, lower_green, upper_green)
                green_ratio = np.sum(green_mask > 0) / cell_area
                # Green grass is a bonus for landing, but only if it's flat (low edges)
                vegetation_bonus = 20 * green_ratio if edge_ratio < 0.1 else 0

                # 4. Obstacle Overlap Penalty
                obstacle_penalty = 0
                overlapping_obstacles = []
                
                for det in detections:
                    ox1, oy1, ox2, oy2 = det["bbox"]
                    
                    # Check intersection between cell rectangle and detection rectangle
                    ix1 = max(x1, ox1)
                    iy1 = max(y1, oy1)
                    ix2 = min(x2, ox2)
                    iy2 = min(y2, oy2)
                    
                    if ix1 < ix2 and iy1 < iy2:
                        # There is overlap
                        overlapping_obstacles.append(det)
                        if det["category"] == "DANGEROUS":
                            obstacle_penalty = 100
                            break  # Maximum penalty
                        elif det["category"] == "CAUTION":
                            # Accumulate or take maximum caution penalty
                            obstacle_penalty = max(obstacle_penalty, 60)

                # Compute final Safety Score
                score = 100 - edge_penalty - texture_penalty - water_penalty - obstacle_penalty + vegetation_bonus
                score = max(0, min(100, int(score)))

                # If there are DANGEROUS obstacles or high water, score is forced to 0
                if obstacle_penalty >= 100 or water_penalty >= 100:
                    score = 0

                is_safe = score >= self.min_safe_score

                zone_info = {
                    "id": f"R{row}C{col}",
                    "row": row,
                    "col": col,
                    "bbox": [x1, y1, x2, y2],
                    "center": [(x1 + x2) // 2, (y1 + y2) // 2],
                    "score": score,
                    "is_safe": is_safe,
                    "edge_ratio": float(edge_ratio),
                    "std_dev": float(std_dev),
                    "water_ratio": float(water_ratio),
                    "green_ratio": float(green_ratio),
                    "obstacles": overlapping_obstacles
                }

                zones.append(zone_info)

                # Keep track of the absolute best zone
                if score > best_score:
                    best_score = score
                    best_zone = zone_info

        return best_zone, zones
