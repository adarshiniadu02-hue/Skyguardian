#!/usr/bin/env python3

import json
import time
from pathlib import Path


# --------------------------------------------------
# SkyGuardian configuration
# --------------------------------------------------

INPUT_FILE = Path("data/live/aircraft.json")
OUTPUT_FILE = Path("data/live/skyguardian_aircraft.json")

RECEIVER_LAT = 52.108889
RECEIVER_LON = 11.615278

# Aircraft must have been heard recently
MAX_SEEN_SECONDS = 15.0


# --------------------------------------------------
# Read readsb aircraft.json
# --------------------------------------------------

def read_aircraft():

    try:
        with open(INPUT_FILE, "r") as f:
            return json.load(f)

    except (FileNotFoundError, json.JSONDecodeError):
        return None


# --------------------------------------------------
# Convert readsb data to SkyGuardian format
# --------------------------------------------------

def map_aircraft(data):

    if data is None:
        return None

    skyguardian_aircraft = []

    for aircraft in data.get("aircraft", []):

        # Ignore aircraft without position
        if "lat" not in aircraft or "lon" not in aircraft:
            continue

        # Ignore stale aircraft
        seen = aircraft.get("seen", 999)

        if seen > MAX_SEEN_SECONDS:
            continue

        mapped = {
            "icao": aircraft.get("hex"),

            "callsign": (
                aircraft.get("flight", "").strip()
                if aircraft.get("flight")
                else ""
            ),

            "latitude": aircraft.get("lat"),
            "longitude": aircraft.get("lon"),

            "altitude_ft": aircraft.get("alt_baro"),
            "geometric_altitude_ft": aircraft.get("alt_geom"),

            "speed_kt": aircraft.get("gs"),
            "heading_deg": aircraft.get("track"),

            "vertical_rate_fpm": aircraft.get("baro_rate"),

            "distance_nm": aircraft.get("dst"),
            "direction_deg": aircraft.get("dir"),

            "seen_sec": seen,
            "position_seen_sec": aircraft.get("seen_pos"),

            "rssi_db": aircraft.get("rssi")
        }

        skyguardian_aircraft.append(mapped)

    # --------------------------------------------------
    # Create final SkyGuardian JSON
    # --------------------------------------------------

    output = {
        "timestamp": data.get("now"),
        "receiver": {
            "latitude": RECEIVER_LAT,
            "longitude": RECEIVER_LON
        },
        "aircraft_count": len(skyguardian_aircraft),
        "aircraft": skyguardian_aircraft
    }

    return output


# --------------------------------------------------
# Main realtime loop
# --------------------------------------------------

def main():

    print("=" * 70)
    print("SKYGUARDIAN — REALTIME AIRCRAFT MAPPER")
    print("=" * 70)

    print(f"Input  : {INPUT_FILE}")
    print(f"Output : {OUTPUT_FILE}")
    print(f"Receiver: {RECEIVER_LAT}, {RECEIVER_LON}")
    print(f"Max aircraft age: {MAX_SEEN_SECONDS} seconds")
    print("-" * 70)

    while True:

        data = read_aircraft()

        result = map_aircraft(data)

        if result is not None:

            # Write JSON atomically
            temp_file = OUTPUT_FILE.with_suffix(".tmp")

            with open(temp_file, "w") as f:
                json.dump(result, f, indent=2)

            temp_file.replace(OUTPUT_FILE)

            print(
                f"\rAircraft: {result['aircraft_count']:3d} | "
                f"Timestamp: {result['timestamp']}",
                end="",
                flush=True
            )

        time.sleep(1)


if __name__ == "__main__":
    main()
