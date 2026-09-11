#!/usr/bin/env python3

import json
import time
from pathlib import Path

BASE_DIR = Path.home() / "ArduinoApps" / "skyguardian2"

INPUT_FILE = BASE_DIR / "data/live/realtime_trajectory.json"
OUTPUT_FILE = BASE_DIR / "data/live/skyguardian_risk.json"


def calculate_risk(aircraft):
    score = 0
    flags = []

    # Large heading change
    heading_change = aircraft.get("heading_change_deg", 0)

    if heading_change > 45:
        score += 30
        flags.append("LARGE_HEADING_CHANGE")

    # Large altitude change
    altitude_change = abs(aircraft.get("altitude_change_ft", 0))

    if altitude_change > 3000:
        score += 25
        flags.append("LARGE_ALTITUDE_CHANGE")

    # High acceleration
    acceleration = abs(aircraft.get("acceleration_mps2", 0))

    if acceleration > 5:
        score += 25
        flags.append("HIGH_ACCELERATION")

    # Large position jump
    distance_jump = aircraft.get("distance_from_previous_m", 0)

    if distance_jump > 5000:
        score += 30
        flags.append("LARGE_POSITION_JUMP")

    # Limit score
    score = min(score, 100)

    if score >= 70:
        risk_level = "ANOMALY"
    elif score >= 40:
        risk_level = "MONITOR"
    else:
        risk_level = "NORMAL"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "flags": flags
    }


def process():
    try:
        with open(INPUT_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    results = []

    for aircraft in data.get("aircraft", []):
        risk = calculate_risk(aircraft)

        result = {
            "icao": aircraft.get("icao"),
            "callsign": aircraft.get("callsign"),
            "latitude": aircraft.get("latitude"),
            "longitude": aircraft.get("longitude"),
            "altitude_ft": aircraft.get("altitude_ft"),
            "speed_kt": aircraft.get("speed_kt"),
            **risk
        }

        results.append(result)

    output = {
        "timestamp": data.get("timestamp"),
        "aircraft_count": len(results),
        "aircraft": results
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(
        f"Risk engine: {len(results)} aircraft processed"
    )


def main():
    print("SkyGuardian Real-Time Risk Engine")
    print("----------------------------------")

    while True:
        process()
        time.sleep(1)


if __name__ == "__main__":
    main()
