#!/bin/bash

set -e

PROJECT="$HOME/ArduinoApps/skyguardian2"
READSB="$PROJECT/readsb"
VENV="$PROJECT/.venv"

echo "============================================================"
echo " SKYGUARDIAN"
echo " Starting complete realtime pipeline"
echo "============================================================"

cd "$PROJECT"

# ------------------------------------------------------------
# Check tmux
# ------------------------------------------------------------

if ! command -v tmux >/dev/null 2>&1; then
    echo "[ERROR] tmux is not installed."
    echo
    echo "Install it with:"
    echo "  sudo apt install tmux"
    exit 1
fi


# ------------------------------------------------------------
# Prevent duplicate instance
# ------------------------------------------------------------

if tmux has-session -t skyguardian 2>/dev/null; then
    echo "[INFO] SKYGUARDIAN is already running."
    echo
    echo "Attach with:"
    echo "  tmux attach -t skyguardian"
    exit 0
fi


# ------------------------------------------------------------
# Start tmux session
# ------------------------------------------------------------

tmux new-session -d -s skyguardian -n pipeline


# ============================================================
# WINDOW 0 — READSB
# ============================================================

tmux send-keys -t skyguardian:pipeline \
    "cd '$READSB' && ./readsb --device-type rtlsdr --device 0 --freq 1090000000 --gain auto --write-json=../data/live --write-json-every=1 --net-api-port=8080" \
    C-m


# ============================================================
# WINDOW 0 — MAPPER
# ============================================================

tmux split-window -h -t skyguardian:pipeline

tmux send-keys -t skyguardian:pipeline.1 \
    "cd '$PROJECT' && python3 python/realtime_mapper.py" \
    C-m


# ============================================================
# WINDOW 0 — TRAJECTORY
# ============================================================

tmux split-window -v -t skyguardian:pipeline.1

tmux send-keys -t skyguardian:pipeline.2 \
    "cd '$PROJECT' && python3 python/realtime_trajectory_tracker.py" \
    C-m


# ============================================================
# WINDOW 0 — ML
# ============================================================

tmux split-window -v -t skyguardian:pipeline.0

tmux send-keys -t skyguardian:pipeline.3 \
    "cd '$PROJECT' && source '$VENV/bin/activate' && python3 python/realtime_ml_detector.py" \
    C-m


# ============================================================
# WINDOW 0 — FUSION
# ============================================================

tmux split-window -h -t skyguardian:pipeline.2

tmux send-keys -t skyguardian:pipeline.4 \
    "cd '$PROJECT' && python3 python/realtime_fusion_engine.py" \
    C-m


# ============================================================
# WINDOW 0 — DASHBOARD / WEBUI
# ============================================================

tmux split-window -v -t skyguardian:pipeline.4

tmux send-keys -t skyguardian:pipeline.5 \
    "cd '$PROJECT' && arduino-app-cli app start '$PROJECT'" \
    C-m


# ------------------------------------------------------------
# Select first pane
# ------------------------------------------------------------

tmux select-pane -t skyguardian:pipeline.0


echo
echo "============================================================"
echo " SKYGUARDIAN STARTED"
echo "============================================================"
echo
echo "Attach to pipeline:"
echo "  tmux attach -t skyguardian"
echo
echo "Detach without stopping:"
echo "  Ctrl+B, then D"
echo
echo "Stop everything:"
echo "  ./stop_skyguardian.sh"
echo "============================================================"


# Attach immediately
tmux attach -t skyguardian
