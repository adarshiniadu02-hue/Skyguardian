#!/usr/bin/env python3

import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FUSION_FILE = BASE_DIR / "data/live/realtime_fusion_results.json"

# Unique fake ICAO so it looks like a newly detected aircraft
FAKE_ICAO = "TEST01"
FAKE_CALLSIGN = "TESTBUZ"

# How long to inject the aircraft
TEST_DURATION = 20

# How often to re-inject it because the real fusion engine
# may overwrite the JSON.
UPDATE_INTERVAL = 0.5


def make_fake_aircraft():
    return {
        "icao": FAKE_ICAO,
        "callsign": FAKE_CALLSIGN,

        # Position near Magdeburg
        "lat": 52.1100,
        "lon": 11.6200,

        # Flight information
        "altitude": 3500,
        "altitude_m": 1067,
        "speed": 120,
        "speed_kts": 120,
        "heading": 90,

        # Risk / ML fields
        "risk_level": "NORMAL",
        "risk_score": 0.10,
        "ml_available": False,
        "ml_anomaly": False,

        # Trajectory fields
        "trajectory": [],
        "history_length": 1,

        # Aviation enrichment
        "registration": "--",
        "country": "TEST",
        "typecode": "TEST",
        "aircraft_name": "SIMULATED TEST AIRCRAFT",
        "aircraft_type": "TEST",
        "airline": "SKYGUARDIAN TEST",
        "operator": "SKYGUARDIAN TEST",
        "route_context": "BUZZER TEST",

        "aviation": {
            "registration": "--",
            "country": "TEST",
            "typecode": "TEST",
            "aircraft_name": "SIMULATED TEST AIRCRAFT",
            "airline": "SKYGUARDIAN TEST",
            "nearest_airport": None,
            "route_context": "BUZZER TEST",
        },
    }


def load_fusion():
    try:
        with open(FUSION_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[TEST] Could not read fusion file: {e}")
        return None


def inject_aircraft(data):
    fake = make_fake_aircraft()

    # Normal SKYGUARDIAN structure:
    # {
    #     "aircraft": [...]
    # }
    if isinstance(data, dict):
        if isinstance(data.get("aircraft"), list):
            aircraft = data["aircraft"]

            # Remove previous copy of our test aircraft
            aircraft[:] = [
                a for a in aircraft
                if str(a.get("icao", "")).upper() != FAKE_ICAO
            ]

            aircraft.append(fake)
            return data

        # Fallback if JSON itself is an aircraft list under another structure
        if "results" in data and isinstance(data["results"], list):
            data["results"] = [
                a for a in data["results"]
                if str(a.get("icao", "")).upper() != FAKE_ICAO
            ]
            data["results"].append(fake)
            return data

    # Fallback: create the standard structure
    return {
        "timestamp": time.time(),
        "aircraft": [fake],
    }


def write_json(data):
    temp_file = FUSION_FILE.with_suffix(".test.tmp")

    with open(temp_file, "w") as f:
        json.dump(data, f, indent=2)

    temp_file.replace(FUSION_FILE)


def main():
    print()
    print("=" * 60)
    print(" SKYGUARDIAN SIMULATED AIRCRAFT / BUZZER TEST")
    print("=" * 60)
    print()
    print(f"ICAO:       {FAKE_ICAO}")
    print(f"Callsign:   {FAKE_CALLSIGN}")
    print(f"Position:   52.1100, 11.6200")
    print(f"Duration:   {TEST_DURATION} seconds")
    print()
    print("Expected:")
    print("  1. NEW AIRCRAFT detected")
    print("  2. One short buzzer beep")
    print("  3. Dashboard shows TESTBUZ")
    print()
    print("Press Ctrl+C to stop.")
    print()

    start = time.time()
    injected_count = 0

    while time.time() - start < TEST_DURATION:
        data = load_fusion()

        if data is not None:
            data = inject_aircraft(data)
            write_json(data)

            injected_count += 1

            if injected_count == 1:
                print("[TEST] Fake aircraft injected!")
            else:
                print(
                    f"[TEST] Keeping fake aircraft alive "
                    f"({int(time.time() - start)}s)"
                )

        time.sleep(UPDATE_INTERVAL)

    print()
    print("[TEST] Test finished.")
    print("[TEST] Stopping injection.")
    print()
    print("The real fusion engine will overwrite the test aircraft.")
    print()


if __name__ == "__main__":
    main()
