
 GARUDA AI — Tactical Ground Control Station & Drone Simulator

This standalone desktop app lets you plan autonomous drone missions, 
analyze ground elevation using custom GeoTIFF maps, and test-fly 
your flight paths in a live interactive simulator with mid-flight 
obstacle avoidance.

 HOW TO RUN (No Setup Required!)

1. Extract/Unzip this entire folder somewhere on your PC.
2. Open the folder and double-click: garuda_gcs_app.exe
3. That's it! Everything is bundled in, so you don't need Python or 
   extra software installed.

 QUICK START GUIDE

1. LOAD MAP: 
   Click 'Load GeoTIFF Map (.tif)' on the left menu to load your 
   terrain elevation map (or use the built-in sample terrain).

2. SET YOUR SURVEY AREA:
   * Click 'Set START Point' -> Click anywhere on the map to set takeoff.
   * Click 'Set GOAL Point'  -> Click on the map for your landing spot.
   * Click 'Add Field Corners' -> Click 3+ points on the map to draw 
     your farm/survey boundary.

3. GENERATE MISSION:
   Hit 'GENERATE MISSION' to calculate the lawnmower grid, coverage 
   area, flight time, and battery usage.

4. TEST FLY IN REAL-TIME:
   Hit 'START TEST FLIGHT'! You'll see a live drone icon take off 
   and fly the pattern. 
   * Use the 'Warp Speed' slider to speed up the flight.
   * Want to test emergency evasive maneuvers? Click 'Drop Hazards' 
     mid-flight directly in front of the drone! It will detect the 
     hazard, execute an evasive detour, and automatically resume the 
     grid to ensure no missed area.


MAP NAVIGATION TIPS

* Zooming: Scroll your mouse wheel forward/backward over the map.
* Panning: Right-click (or middle-click) and drag the mouse.
* Reset View: Click 'Fit Map View' above the map to center everything.
* 
EXPORTED WAYPOINTS

When you generate a mission, the app auto-saves a standard MAVLink 
file ('garuda_master_mission.waypoints') right into this folder. 
You can upload this file directly into Mission Planner or 
QGroundControl for real drone hardware!

Have fun testing! Built for UAV operators and field survey missions.
