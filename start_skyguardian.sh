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
# Create tmux session
# ------------------------------------------------------------

tmux new-session -d -s skyguardian -n pipeline


# ------------------------------------------------------------
# Store stable pane IDs
#
# IMPORTANT:
# We use pane IDs instead of pane numbers because tmux can
# renumber panes after split-window operations.
# ------------------------------------------------------------

P0=$(tmux display-message -t skyguardian:pipeline -p '#{pane_id}')


# ============================================================
# READSB
# ============================================================

tmux send-keys -t "$P0" \
"cd '$READSB' && ./readsb --device-type rtlsdr --device 0 --freq 1090000000 --gain auto --write-json=../data/live --write-json-every=1 --net-api-port=8080" C-m


# ============================================================
# MAPPER
# ============================================================

P1=$(tmux split-window -h -t "$P0" -P -F '#{pane_id}')

tmux send-keys -t "$P1" \
"cd '$PROJECT' && python3 python/realtime_mapper.py" C-m


# ============================================================
# TRAJECTORY
# ============================================================

P2=$(tmux split-window -v -t "$P1" -P -F '#{pane_id}')

tmux send-keys -t "$P2" \
"cd '$PROJECT' && python3 python/realtime_trajectory_tracker.py" C-m


# ============================================================
# ML
# ============================================================

P3=$(tmux split-window -v -t "$P0" -P -F '#{pane_id}')

tmux send-keys -t "$P3" \
"cd '$PROJECT' && source '$VENV/bin/activate' && python3 python/realtime_ml_detector.py" C-m


# ============================================================
# FUSION
# ============================================================

P4=$(tmux split-window -h -t "$P2" -P -F '#{pane_id}')

tmux send-keys -t "$P4" \
"cd '$PROJECT' && python3 python/realtime_fusion_engine.py" C-m


# ============================================================
# ARDUINO APP / WEBUI
# ============================================================

P5=$(tmux split-window -v -t "$P4" -P -F '#{pane_id}')

tmux send-keys -t "$P5" \
"cd '$PROJECT' && arduino-app-cli app start '$PROJECT'" C-m


# ------------------------------------------------------------
# Select READSB pane
# ------------------------------------------------------------

tmux select-pane -t "$P0"


echo
echo "============================================================"
echo " SKYGUARDIAN STARTED"
echo "============================================================"
echo
echo "Pipeline:"
echo
echo "  READSB"
echo "     ↓"
echo "  MAPPER"
echo "     ↓"
echo "  TRAJECTORY"
echo "     ↓"
echo "  ML"
echo "     ↓"
echo "  FUSION"
echo "     ↓"
echo "  WEBUI + MCU BUZZER"
echo
echo "Detach:"
echo "  Ctrl+B, then D"
echo
echo "Stop:"
echo "  ./stop_skyguardian.sh"
echo "============================================================"


# ------------------------------------------------------------
# Attach
# ------------------------------------------------------------

tmux attach -t skyguardian
