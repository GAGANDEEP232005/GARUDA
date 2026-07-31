"""
================================================================================
GARUDA AI: Tactical Ground Control Station (GCS)
Curved Side-Bypass Engine (Matches Hand-Drawn Curve Around Hazard)
Filename: garuda_gcs_app.py
================================================================================
"""

import sys
import os
import math
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QGroupBox, QTextEdit, QSplitter, QSlider
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class TacticalGCSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GARUDA AI :: Curved Side-Bypass Engine")
        self.setGeometry(100, 100, 1200, 750)

        # Simulation & Waypoint Data
        self.planned_waypoints = []
        self.active_waypoints = []
        self.drone_pos = [0.0, 0.0]
        self.current_wpt_idx = 0
        self.hazards = []
        self.handled_hazards = set()
        self.click_mode = "NONE"

        self.init_ui()

        # Simulation Timer Loop
        self.timer = QTimer()
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.update_simulation)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_layout_widget := QWidget())
        main_layout = QHBoxLayout(main_layout_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Controls Panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        grp_file = QGroupBox("WAYPOINT FILE IMPORTER")
        file_layout = QVBoxLayout()
        
        self.btn_load_wpt = QPushButton("📂 Load Waypoints File (.waypoints / .txt)")
        self.btn_load_wpt.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: bold; padding: 10px;")
        self.btn_load_wpt.clicked.connect(self.load_waypoints_file)
        file_layout.addWidget(self.btn_load_wpt)
        grp_file.setLayout(file_layout)
        left_layout.addWidget(grp_file)

        grp_sim = QGroupBox("SIMULATOR CONTROLS")
        sim_layout = QVBoxLayout()
        
        self.btn_start = QPushButton("▶ START TEST FLIGHT")
        self.btn_start.setStyleSheet("background-color: #00e676; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self.toggle_simulation)

        self.btn_drop_click = QPushButton("🎯 CLICK MAP TO DROP HAZARD")
        self.btn_drop_click.setStyleSheet("background-color: #f59e0b; font-weight: bold; padding: 10px;")
        self.btn_drop_click.clicked.connect(self.enable_click_hazard_mode)

        self.btn_reset = QPushButton("🔄 RESET SIMULATOR")
        self.btn_reset.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; padding: 10px;")
        self.btn_reset.clicked.connect(self.reset_simulation)

        sim_layout.addWidget(self.btn_start)
        sim_layout.addWidget(self.btn_drop_click)
        sim_layout.addWidget(self.btn_reset)
        sim_layout.addWidget(QLabel("Simulation Speed Multiplier:"))
        
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(1, 10)
        self.slider_speed.setValue(3)
        sim_layout.addWidget(self.slider_speed)

        grp_sim.setLayout(sim_layout)
        left_layout.addWidget(grp_sim)
        left_layout.addStretch()

        # Center Matplotlib Canvas
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        self.figure, self.ax = plt.subplots(figsize=(7, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        center_layout.addWidget(self.canvas)

        # Right Log Console
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        grp_log = QGroupBox("MAVLINK TELEMETRY & LIVE LOG")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        grp_log.setLayout(log_layout)
        right_layout.addWidget(grp_log)

        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([280, 620, 300])

        main_layout.addWidget(splitter)
        self.redraw_plot()
        self.log("System Ready. Load waypoints file or start simulator.")

    def log(self, text):
        self.log_text.append(f"> {text}")

    def enable_click_hazard_mode(self):
        self.click_mode = "HAZARD"
        self.log("[MODE] Click hazard placement enabled! Click anywhere on the map to place an obstacle.")

    def on_map_click(self, event):
        if self.click_mode == "HAZARD" and event.xdata is not None and event.ydata is not None:
            hz_pt = (event.xdata, event.ydata)
            self.hazards.append(hz_pt)
            self.click_mode = "NONE"
            self.log(f"[HAZARD PLACED] Obstacle added at ({event.xdata:.1f}, {event.ydata:.1f}).")
            self.redraw_plot()

    def load_waypoints_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Waypoint File", "", "Waypoint Files (*.waypoints *.txt)"
        )
        if not file_path:
            return

        self.log(f"Reading waypoints file: {file_path}")
        parsed_points = []

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith("QGC WPL"):
                    continue

                parts = line.split("\t")
                if len(parts) >= 10:
                    try:
                        lat = float(parts[8])
                        lon = float(parts[9])
                        if lat != 0.0 and lon != 0.0:
                            parsed_points.append((lon, lat))
                    except ValueError:
                        continue

            if parsed_points:
                lons = [p[0] for p in parsed_points]
                lats = [p[1] for p in parsed_points]
                min_lon, max_lon = min(lons), max(lons)
                min_lat, max_lat = min(lats), max(lats)

                scale_x = (max_lon - min_lon) if (max_lon - min_lon) != 0 else 1.0
                scale_y = (max_lat - min_lat) if (max_lat - min_lat) != 0 else 1.0

                self.planned_waypoints = [
                    (10.0 + ((p[0] - min_lon) / scale_x) * 80.0, 
                     10.0 + ((p[1] - min_lat) / scale_y) * 80.0) 
                    for p in parsed_points
                ]

                self.reset_simulation()
                self.log(f"[SUCCESS] Loaded {len(self.planned_waypoints)} waypoints!")
            else:
                self.log("[ERROR] No valid lat/long coordinate waypoints found in file.")

        except Exception as e:
            self.log(f"[ERROR] Failed to parse file: {str(e)}")

    def toggle_simulation(self):
        if not self.active_waypoints:
            self.log("[ERROR] Load a waypoint file first!")
            return

        if self.timer.isActive():
            self.timer.stop()
            self.btn_start.setText("▶ RESUME TEST FLIGHT")
            self.log("Simulation paused.")
        else:
            self.timer.start()
            self.btn_start.setText("⏸ PAUSE TEST FLIGHT")
            self.log("Takeoff! Executing waypoint survey flight...")

    def reset_simulation(self):
        self.timer.stop()
        self.btn_start.setText("▶ START TEST FLIGHT")
        self.active_waypoints = list(self.planned_waypoints)
        if self.active_waypoints:
            self.drone_pos = list(self.active_waypoints[0])
        else:
            self.drone_pos = [0.0, 0.0]
        self.current_wpt_idx = 0
        self.hazards = []
        self.handled_hazards.clear()
        self.click_mode = "NONE"
        self.redraw_plot()

    def generate_side_bypass_curve(self, curr_pos, hazard_pos, target_pos, offset_dist=10.0):
        """Generates 3 points that curve cleanly around the side of the hazard"""
        dx = target_pos[0] - curr_pos[0]
        dy = target_pos[1] - curr_pos[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return []

        fx, fy = dx / dist, dy / dist  # Forward direction vector
        rx, ry = -fy, fx               # Right side perpendicular vector

        # 1. Veer Right BEFORE the hazard
        p1 = (hazard_pos[0] + rx * offset_dist - fx * 5.0, 
              hazard_pos[1] + ry * offset_dist - fy * 5.0)

        # 2. Fly Parallel beside the hazard
        p2 = (hazard_pos[0] + rx * offset_dist + fx * 3.0, 
              hazard_pos[1] + ry * offset_dist + fy * 3.0)

        # 3. Curve back to the track AFTER the hazard
        p3 = (hazard_pos[0] + fx * (offset_dist + 2.0), 
              hazard_pos[1] + fy * (offset_dist + 2.0))

        return [p1, p2, p3]

    def update_simulation(self):
        if self.current_wpt_idx >= len(self.active_waypoints):
            self.timer.stop()
            self.btn_start.setText("▶ START TEST FLIGHT")
            self.log("[MISSION COMPLETE] Waypoint survey completed! Landed safely.")
            return

        target = self.active_waypoints[self.current_wpt_idx]

        # PROXIMITY RADAR: Check if drone is approaching a hazard on the track
        for hz_idx, hz in enumerate(self.hazards):
            if hz_idx in self.handled_hazards:
                continue

            dist_drone_to_hz = math.hypot(self.drone_pos[0] - hz[0], self.drone_pos[1] - hz[1])

            # Trigger when drone gets within 10 units of the hazard
            if dist_drone_to_hz < 10.0:
                self.log(f"[HAZARD DETECTED] Obstacle H{hz_idx + 1} ahead! Executing side-curve bypass around hazard...")
                self.handled_hazards.add(hz_idx)

                # Generate the 3-point side curve
                bypass_curve = self.generate_side_bypass_curve(self.drone_pos, hz, target, offset_dist=10.0)

                # Remove the blocked waypoint and insert the side curve points
                self.active_waypoints = (
                    self.active_waypoints[:self.current_wpt_idx] + 
                    bypass_curve + 
                    self.active_waypoints[self.current_wpt_idx + 1:]
                )

                self.log("[PLANNER] Side-curve injected! Bypassing obstacle cleanly...")
                self.redraw_plot()
                return

        # Move drone smoothly towards current waypoint
        dx = target[0] - self.drone_pos[0]
        dy = target[1] - self.drone_pos[1]
        dist = math.hypot(dx, dy)
        speed = self.slider_speed.value() * 1.2

        if dist <= speed:
            self.drone_pos = list(target)
            self.current_wpt_idx += 1
        else:
            self.drone_pos[0] += (dx / dist) * speed
            self.drone_pos[1] += (dy / dist) * speed

        self.redraw_plot()

    def redraw_plot(self):
        self.ax.clear()
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.set_title("GARUDA AI :: Curved Side-Bypass Engine", fontsize=10, fontweight='bold')
        self.ax.grid(True, linestyle='--', alpha=0.4)

        if self.active_waypoints:
            wpt_x = [pt[0] for pt in self.active_waypoints]
            wpt_y = [pt[1] for pt in self.active_waypoints]
            self.ax.plot(wpt_x, wpt_y, 'g--', alpha=0.6, label="Active Route")
            self.ax.scatter(wpt_x, wpt_y, c='green', s=30, label="Waypoints")

        for hz in self.hazards:
            self.ax.scatter(hz[0], hz[1], c='red', s=150, marker='o', label="Hazard")

        if self.active_waypoints:
            self.ax.scatter(self.drone_pos[0], self.drone_pos[1], c='blue', s=120, marker='P', label="UAV GARUDA-1")

        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=8)

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TacticalGCSWindow()
    window.show()
    sys.exit(app.exec())