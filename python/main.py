#!/usr/bin/env python3

import json
import math
import time
from pathlib import Path

from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI


# ============================================================
# SKYGUARDIAN
# REALTIME FUSION → WEB DASHBOARD
# ============================================================

print("=" * 70)
print("SKYGUARDIAN — EDGE AI FLIGHT MONITORING")
print("REALTIME FUSION → WEBUI")
print("=" * 70)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FUSION_FILE = BASE_DIR / "data/live/realtime_fusion_results.json"


# ============================================================
# RECEIVER LOCATION
# ============================================================

RECEIVER_LAT = 52.108889
RECEIVER_LON = 11.615278


# ============================================================
# UPDATE SETTINGS
# ============================================================

UPDATE_INTERVAL = 1.0


# ============================================================
# WEB UI
# ============================================================

ui = WebUI()


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if value is None:
            return default

        return float(value)

    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert a value to int."""
    try:
        if value is None:
            return default

        return int(value)

    except (ValueError, TypeError):
        return default


def read_fusion_results():
    """Read the latest fusion-engine output."""

    try:
        with open(FUSION_FILE, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        return None

    except json.JSONDecodeError:
        return None

    except Exception as e:
        print(f"[WEBUI] Read error: {e}", flush=True)
        return None


# ============================================================
# DISTANCE / RADAR COORDINATES
# ============================================================

def calculate_xy(latitude, longitude):
    """
    Convert latitude/longitude into approximate
    local X/Y coordinates in kilometers.

    X = east/west
    Y = north/south
    """

    lat = safe_float(latitude)
    lon = safe_float(longitude)

    lat_diff = lat - RECEIVER_LAT
    lon_diff = lon - RECEIVER_LON

    # Approximate km per degree
    km_per_lat = 111.32

    km_per_lon = 111.32 * math.cos(
        math.radians(RECEIVER_LAT)
    )

    x = lon_diff * km_per_lon
    y = lat_diff * km_per_lat

    return x, y


# ============================================================
# ALTITUDE NORMALIZATION
# ============================================================

def get_altitude_m(aircraft):
    """
    Return altitude in meters.

    Priority:
        altitude_m
        altitude_ft
        altitude
    """

    if aircraft.get("altitude_m") is not None:
        return safe_float(
            aircraft.get("altitude_m")
        )

    if aircraft.get("altitude_ft") is not None:
        return safe_float(
            aircraft.get("altitude_ft")
        ) * 0.3048

    altitude = safe_float(
        aircraft.get("altitude"),
        0.0
    )

    # If the fusion engine already provides altitude
    # without a unit, assume meters.
    return altitude


# ============================================================
# SPEED NORMALIZATION
# ============================================================

def get_speed_mps(aircraft):
    """
    Return speed in meters/second.

    Priority:
        speed_mps
        speed_kt
        speed
    """

    if aircraft.get("speed_mps") is not None:
        return safe_float(
            aircraft.get("speed_mps")
        )

    if aircraft.get("speed_kt") is not None:
        return safe_float(
            aircraft.get("speed_kt")
        ) * 0.514444

    return safe_float(
        aircraft.get("speed"),
        0.0
    )


# ============================================================
# BUILD DASHBOARD AIRCRAFT OBJECT
# ============================================================

def convert_aircraft(aircraft):
    """
    Convert fusion-engine aircraft data into the
    format expected by the SkyGuardian dashboard.
    """

    latitude = safe_float(
        aircraft.get("latitude")
    )

    longitude = safe_float(
        aircraft.get("longitude")
    )

    x, y = calculate_xy(
        latitude,
        longitude
    )

    altitude_m = get_altitude_m(
        aircraft
    )

    speed_mps = get_speed_mps(
        aircraft
    )

    altitude_ft = altitude_m / 0.3048
    speed_kt = speed_mps / 0.514444

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    icao = aircraft.get(
        "icao",
        ""
    )

    callsign = aircraft.get(
        "callsign",
        ""
    )

    # --------------------------------------------------------
    # Risk / Fusion
    # --------------------------------------------------------

    risk_level = aircraft.get(
        "risk_level",
        aircraft.get(
            "status",
            "NORMAL"
        )
    )

    final_score = safe_float(
        aircraft.get(
            "final_score",
            aircraft.get(
                "risk",
                0
            )
        )
    )

    rule_score = safe_float(
        aircraft.get(
            "rule_score",
            0
        )
    )

    ml_score = safe_float(
        aircraft.get(
            "ml_anomaly_score",
            aircraft.get(
                "ml_score",
                0
            )
        )
    )

    ml_classification = aircraft.get(
        "ml_classification",
        aircraft.get(
            "ml_class",
            "NORMAL"
        )
    )

    ml_available = aircraft.get(
        "ml_available",
        False
    )

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    explanation = aircraft.get(
        "explanation",
        aircraft.get(
            "anomaly_explanation",
            "NO_SIGNIFICANT_ANOMALY"
        )
    )

    # --------------------------------------------------------
    # Trajectory features
    # --------------------------------------------------------

    distance_previous = safe_float(
        aircraft.get(
            "distance_from_previous_m",
            0
        )
    )

    time_delta = safe_float(
        aircraft.get(
            "time_delta_s",
            0
        )
    )

    altitude_change = safe_float(
        aircraft.get(
            "altitude_change_m",
            0
        )
    )

    speed_change = safe_float(
        aircraft.get(
            "speed_change_mps",
            0
        )
    )

    heading_change = safe_float(
        aircraft.get(
            "heading_change_deg",
            0
        )
    )

    calculated_speed = safe_float(
        aircraft.get(
            "calculated_speed_mps",
            0
        )
    )

    acceleration = safe_float(
        aircraft.get(
            "acceleration_mps2",
            0
        )
    )

    # --------------------------------------------------------
    # Position / heading
    # --------------------------------------------------------

    heading = safe_float(
        aircraft.get(
            "heading_deg",
            aircraft.get(
                "heading",
                0
            )
        )
    )

    vertical_rate = safe_float(
        aircraft.get(
            "vertical_rate_fpm",
            0
        )
    )

    distance_nm = safe_float(
        aircraft.get(
            "distance_nm",
            0
        )
    )

    # --------------------------------------------------------
    # Final dashboard object
    # --------------------------------------------------------

    return {

        # Identity
        "icao": icao,
        "callsign": callsign,

        # Position
        "latitude": latitude,
        "longitude": longitude,
        "x": x,
        "y": y,

        # Flight data
        "altitude": altitude_m,
        "altitude_m": altitude_m,
        "altitude_ft": altitude_ft,

        "speed": speed_mps,
        "speed_mps": speed_mps,
        "speed_kt": speed_kt,

        "heading": heading,
        "heading_deg": heading,

        "vertical_rate_fpm": vertical_rate,

        "distance_nm": distance_nm,

        # Fusion
        "risk": final_score,
        "final_score": final_score,
        "risk_level": risk_level,
        "status": risk_level,

        # Rule engine
        "rule_score": rule_score,

        # Machine learning
        "ml_score": ml_score,
        "ml_anomaly_score": ml_score,
        "ml_class": ml_classification,
        "ml_classification": ml_classification,
        "ml_available": ml_available,

        # Explanation
        "explanation": explanation,
        "anomaly_explanation": explanation,

        # Trajectory features
        "distance_from_previous_m": distance_previous,
        "time_delta_s": time_delta,
        "altitude_change_m": altitude_change,
        "speed_change_mps": speed_change,
        "heading_change_deg": heading_change,
        "calculated_speed_mps": calculated_speed,
        "acceleration_mps2": acceleration,

        # Tracker state
        "position_updated": aircraft.get(
            "position_updated",
            True
        ),

        "history_length": safe_int(
            aircraft.get(
                "history_length",
                0
            )
        )
    }


# ============================================================
# BUILD COMPLETE DASHBOARD PAYLOAD
# ============================================================

def build_dashboard_payload(data):
    """
    Convert fusion-engine JSON into the WebUI payload.
    """

    if data is None:
        return {
            "timestamp": time.time(),
            "aircraft_count": 0,
            "aircraft": []
        }

    aircraft_list = data.get(
        "aircraft",
        []
    )

    # Protect against malformed fusion data
    if not isinstance(aircraft_list, list):
        aircraft_list = []

    dashboard_aircraft = []

    for aircraft in aircraft_list:

        if not isinstance(aircraft, dict):
            continue

        try:
            converted = convert_aircraft(
                aircraft
            )

            dashboard_aircraft.append(
                converted
            )

        except Exception as e:
            print(
                f"[WEBUI] Aircraft conversion error: {e}",
                flush=True
            )

    return {
        "timestamp": data.get(
            "timestamp",
            time.time()
        ),

        "aircraft_count": len(
            dashboard_aircraft
        ),

        "aircraft": dashboard_aircraft
    }


# ============================================================
# SEND DATA TO WEB UI
# ============================================================

def send_dashboard_update(payload):
    """
    Send the latest aircraft state to the frontend.
    """

    try:
        ui.send_message(
            "aircraft_update",
            payload
        )

        return True

    except Exception as e:
        print(
            f"[WEBUI] Send error: {e}",
            flush=True
        )

        return False


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    """
    Continuously read fusion results and update
    the SkyGuardian dashboard.
    """

    print()
    print("Fusion input:")
    print(FUSION_FILE)

    print()
    print("Receiver:")
    print(
        f"{RECEIVER_LAT}, {RECEIVER_LON}"
    )

    print()
    print("Dashboard update interval:")
    print(
        f"{UPDATE_INTERVAL} second"
    )

    print()
    print("-" * 70)
    print("Waiting for realtime fusion data...")
    print("-" * 70)

    last_timestamp = None

    while True:

        try:

            # ------------------------------------------------
            # Read latest fusion data
            # ------------------------------------------------

            data = read_fusion_results()

            if data is None:

                print(
                    "[WEBUI] Waiting for fusion results...",
                    flush=True
                )

                time.sleep(
                    UPDATE_INTERVAL
                )

                continue

            # ------------------------------------------------
            # Build dashboard payload
            # ------------------------------------------------

            payload = build_dashboard_payload(
                data
            )

            # ------------------------------------------------
            # Send to browser
            # ------------------------------------------------

            sent = send_dashboard_update(
                payload
            )

            # ------------------------------------------------
            # Console information
            # ------------------------------------------------

            timestamp = payload.get(
                "timestamp"
            )

            aircraft_count = payload.get(
                "aircraft_count",
                0
            )

            risk_counts = {
                "NORMAL": 0,
                "MONITOR": 0,
                "ANOMALY": 0
            }

            for aircraft in payload.get(
                "aircraft",
                []
            ):

                risk = str(
                    aircraft.get(
                        "risk_level",
                        "NORMAL"
                    )
                ).upper()

                if risk in risk_counts:
                    risk_counts[risk] += 1

            # ------------------------------------------------
            # Print only when timestamp changes
            # ------------------------------------------------

            if timestamp != last_timestamp:

                print(
                    f"[WEBUI] Aircraft: {aircraft_count:3d} | "
                    f"Normal: {risk_counts['NORMAL']:3d} | "
                    f"Monitor: {risk_counts['MONITOR']:3d} | "
                    f"Anomaly: {risk_counts['ANOMALY']:3d} | "
                    f"Sent: {sent}",
                    flush=True
                )

                last_timestamp = timestamp

            time.sleep(
                UPDATE_INTERVAL
            )

        except KeyboardInterrupt:

            print()
            print(
                "SkyGuardian dashboard stopped.",
                flush=True
            )

            break

        except Exception as e:

            print(
                f"[WEBUI] Main loop error: {e}",
                flush=True
            )

            time.sleep(
                UPDATE_INTERVAL
            )


# ============================================================
# START ARDUINO APP
# ============================================================

if __name__ == "__main__":

    try:

        print()
        print("Starting SkyGuardian...")
        print()

        # IMPORTANT:
        # Arduino AppController is an object, not a callable.
        # App.run() starts registered bricks such as WebUI
        # and executes the user loop.
        App.run(
            user_loop=main
        )

    except KeyboardInterrupt:

        print()
        print(
            "SkyGuardian stopped.",
            flush=True
        )

    except Exception as e:

        print(
            f"[FATAL] SkyGuardian WebUI error: {e}",
            flush=True
        )
