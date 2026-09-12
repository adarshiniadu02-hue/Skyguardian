#!/bin/bash

PROJECT="$HOME/ArduinoApps/skyguardian2"

echo "============================================================"
echo " SKYGUARDIAN"
echo " Stopping complete realtime pipeline"
echo "============================================================"

# ------------------------------------------------------------
# Stop Arduino App
# ------------------------------------------------------------

arduino-app-cli app stop "$PROJECT" 2>/dev/null || true


# ------------------------------------------------------------
# Stop tmux pipeline
# ------------------------------------------------------------

if tmux has-session -t skyguardian 2>/dev/null; then
    tmux kill-session -t skyguardian
fi


# ------------------------------------------------------------
# Safety cleanup
# ------------------------------------------------------------

pkill -f "$PROJECT/python/realtime_mapper.py" 2>/dev/null || true
pkill -f "$PROJECT/python/realtime_trajectory_tracker.py" 2>/dev/null || true
pkill -f "$PROJECT/python/realtime_ml_detector.py" 2>/dev/null || true
pkill -f "$PROJECT/python/realtime_fusion_engine.py" 2>/dev/null || true


echo
echo "SKYGUARDIAN stopped."
echo
