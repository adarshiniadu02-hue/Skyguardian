#!/usr/bin/env python3

import json
import urllib.request
import math
import time

# --------------------------------------------------
# SkyGuardian receiver location
# --------------------------------------------------

CENTER_LAT = 52.108889
CENTER_LON = 11.615278

# 100 km ≈ 54 nautical miles
RADIUS_NM = 54

API_URL = (
    f"http://127.0.0.1:8080/"
    f"?circle={CENTER_LAT},{CENTER_LON},{RADIUS_NM}"
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def altitude_value(a):
    alt = a.get("alt_baro")

    if alt == "ground":
        return 0

    if alt is None:
        return None

    return alt


def get_aircraft():

    try:
        with urllib.request.urlopen(API_URL, timeout=3) as response:
            return json.load(response)

    except Exception as e:
        print("ERROR connecting to readsb:", e)
        return None


# --------------------------------------------------
# Main loop
# --------------------------------------------------

while True:

    data = get_aircraft()

    if data is None:
        time.sleep(2)
        continue

    aircraft = data.get("aircraft", [])

    # Clear terminal
    print("\033[2J\033[H", end="")

    print("=" * 90)
    print("              SKYGUARDIAN — 100 KM AIRCRAFT AREA")
    print("=" * 90)

    print(
        f"Center : {CENTER_LAT:.6f}, {CENTER_LON:.6f}"
    )

    print(
        f"Radius : {RADIUS_NM:.0f} NM (~100 km)"
    )

    print(
        f"Readsb time : {data.get('now')}"
    )

    print(
        f"Aircraft in area : {len(aircraft)}"
    )

    print("=" * 90)

    print(
        f"{'ICAO':<8}"
        f"{'CALLSIGN':<12}"
        f"{'ALT(ft)':>9}"
        f"{'SPEED':>9}"
        f"{'TRACK':>9}"
        f"{'DIST(NM)':>10}"
        f"{'DIR':>8}"
        f"{'SEEN':>8}"
    )

    print("-" * 90)

    # Sort nearest first
    aircraft.sort(key=lambda x: x.get("dst", 9999))

    for a in aircraft:

        hex_id = a.get("hex", "?")

        callsign = a.get("flight", "").strip()

        if not callsign:
            callsign = "-"

        altitude = altitude_value(a)

        if altitude is None:
            altitude_text = "-"
        else:
            altitude_text = f"{altitude:.0f}"

        speed = a.get("gs")

        if speed is None:
            speed_text = "-"
        else:
            speed_text = f"{speed:.0f} kt"

        track = a.get("track")

        if track is None:
            track_text = "-"
        else:
            track_text = f"{track:.0f}°"

        distance = a.get("dst")

        if distance is None:
            distance_text = "-"
        else:
            distance_text = f"{distance:.1f}"

        direction = a.get("dir")

        if direction is None:
            direction_text = "-"
        else:
            direction_text = f"{direction:.0f}°"

        seen = a.get("seen")

        if seen is None:
            seen_text = "-"
        else:
            seen_text = f"{seen:.1f}s"

        print(
            f"{hex_id:<8}"
            f"{callsign:<12}"
            f"{altitude_text:>9}"
            f"{speed_text:>9}"
            f"{track_text:>9}"
            f"{distance_text:>10}"
            f"{direction_text:>8}"
            f"{seen_text:>8}"
        )

    print("-" * 90)

    print("Updating every 2 seconds...  Ctrl+C to stop.")

    time.sleep(2)
