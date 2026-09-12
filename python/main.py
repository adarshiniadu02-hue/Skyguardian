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

# Final AI fusion output
FUSION_FILE = (
    BASE_DIR
    / "data/live/realtime_fusion_results.json"
)

# Aviation-enriched aircraft data produced by realtime_mapper.py
AVIATION_FILE = (
    BASE_DIR
    / "data/live/skyguardian_aircraft.json"
)


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

    except (
        ValueError,
        TypeError
    ):

        return default


def safe_int(value, default=0):
    """Safely convert a value to int."""

    try:

        if value is None:
            return default

        return int(value)

    except (
        ValueError,
        TypeError
    ):

        return default


# ============================================================
# READ JSON
# ============================================================

def read_json_file(path):
    """
    Read a JSON file safely.
    """

    try:

        with open(
            path,
            "r"
        ) as f:

            return json.load(f)

    except FileNotFoundError:

        return None

    except json.JSONDecodeError:

        return None

    except Exception as e:

        print(
            f"[WEBUI] Read error {path}: {e}",
            flush=True
        )

        return None


# ============================================================
# READ FUSION RESULTS
# ============================================================

def read_fusion_results():
    """
    Read the latest fusion-engine output.
    """

    return read_json_file(
        FUSION_FILE
    )


# ============================================================
# READ AVIATION DATA
# ============================================================

def read_aviation_data():
    """
    Read the latest aviation-enriched aircraft data
    produced by realtime_mapper.py.
    """

    return read_json_file(
        AVIATION_FILE
    )


# ============================================================
# BUILD AVIATION LOOKUP
# ============================================================

def build_aviation_lookup(data):
    """
    Build:

        ICAO -> aviation metadata

    from skyguardian_aircraft.json.

    This allows the dashboard to preserve aviation
    enrichment even though the current fusion engine
    does not copy the aviation object into its output.
    """

    lookup = {}

    if not isinstance(
        data,
        dict
    ):

        return lookup

    aircraft_list = data.get(
        "aircraft",
        []
    )

    if not isinstance(
        aircraft_list,
        list
    ):

        return lookup

    for aircraft in aircraft_list:

        if not isinstance(
            aircraft,
            dict
        ):

            continue

        icao = aircraft.get(
            "icao"
        )

        if not icao:

            continue

        icao = str(
            icao
        ).strip().upper()

        aviation = aircraft.get(
            "aviation"
        )

        if not isinstance(
            aviation,
            dict
        ):

            aviation = {}

        lookup[icao] = aviation

    return lookup


# ============================================================
# DISTANCE / RADAR COORDINATES
# ============================================================

def calculate_xy(
    latitude,
    longitude
):
    """
    Convert latitude/longitude into approximate
    local X/Y coordinates in kilometers.

    X = east/west
    Y = north/south
    """

    lat = safe_float(
        latitude
    )

    lon = safe_float(
        longitude
    )

    lat_diff = (
        lat
        -
        RECEIVER_LAT
    )

    lon_diff = (
        lon
        -
        RECEIVER_LON
    )

    # Approximate km per degree
    km_per_lat = 111.32

    km_per_lon = (
        111.32
        *
        math.cos(
            math.radians(
                RECEIVER_LAT
            )
        )
    )

    x = (
        lon_diff
        *
        km_per_lon
    )

    y = (
        lat_diff
        *
        km_per_lat
    )

    return x, y


# ============================================================
# ALTITUDE NORMALIZATION
# ============================================================

def get_altitude_m(
    aircraft
):
    """
    Return altitude in meters.

    Priority:
        altitude_m
        altitude_ft
        altitude
    """

    if aircraft.get(
        "altitude_m"
    ) is not None:

        return safe_float(
            aircraft.get(
                "altitude_m"
            )
        )

    if aircraft.get(
        "altitude_ft"
    ) is not None:

        return (
            safe_float(
                aircraft.get(
                    "altitude_ft"
                )
            )
            *
            0.3048
        )

    altitude = safe_float(
        aircraft.get(
            "altitude",
            0.0
        )
    )

    # Fusion engine's generic altitude field is meters.
    return altitude


# ============================================================
# SPEED NORMALIZATION
# ============================================================

def get_speed_mps(
    aircraft
):
    """
    Return speed in meters/second.

    Priority:
        speed_mps
        speed_kt
        speed
    """

    if aircraft.get(
        "speed_mps"
    ) is not None:

        return safe_float(
            aircraft.get(
                "speed_mps"
            )
        )

    if aircraft.get(
        "speed_kt"
    ) is not None:

        return (
            safe_float(
                aircraft.get(
                    "speed_kt"
                )
            )
            *
            0.514444
        )

    return safe_float(
        aircraft.get(
            "speed",
            0.0
        )
    )


# ============================================================
# AVIATION VALUE HELPER
# ============================================================

def aviation_value(
    aviation,
    key,
    default="--"
):
    """
    Safely retrieve a value from the aviation metadata.
    """

    if not isinstance(
        aviation,
        dict
    ):

        return default

    value = aviation.get(
        key
    )

    if value is None:

        return default

    if isinstance(
        value,
        str
    ):

        value = value.strip()

        if not value:

            return default

    return value


# ============================================================
# BUILD DASHBOARD AIRCRAFT OBJECT
# ============================================================

def convert_aircraft(
    aircraft,
    aviation_lookup=None
):
    """
    Convert fusion-engine aircraft data into the
    format expected by the SkyGuardian dashboard.

    Aviation enrichment is merged from
    skyguardian_aircraft.json using ICAO.
    """

    if aviation_lookup is None:

        aviation_lookup = {}

    # --------------------------------------------------------
    # Position
    # --------------------------------------------------------

    latitude = safe_float(
        aircraft.get(
            "latitude"
        )
    )

    longitude = safe_float(
        aircraft.get(
            "longitude"
        )
    )

    x, y = calculate_xy(
        latitude,
        longitude
    )

    # --------------------------------------------------------
    # Flight data
    # --------------------------------------------------------

    altitude_m = get_altitude_m(
        aircraft
    )

    speed_mps = get_speed_mps(
        aircraft
    )

    altitude_ft = (
        altitude_m
        /
        0.3048
    )

    speed_kt = (
        speed_mps
        /
        0.514444
    )

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    icao = aircraft.get(
        "icao",
        ""
    )

    if icao:

        icao = str(
            icao
        ).strip().upper()

    callsign = aircraft.get(
        "callsign",
        ""
    )

    # --------------------------------------------------------
    # Aviation enrichment
    # --------------------------------------------------------

    aviation = aviation_lookup.get(
        icao,
        {}
    )

    if not isinstance(
        aviation,
        dict
    ):

        aviation = {}

    # --------------------------------------------------------
    # Support possible alternate aviation field names
    # --------------------------------------------------------

    registration = aviation_value(
        aviation,
        "registration"
    )

    country = aviation_value(
        aviation,
        "country"
    )

    typecode = aviation_value(
        aviation,
        "typecode"
    )

    aircraft_name = aviation_value(
        aviation,
        "aircraft_name"
    )

    # Current mapper uses "airline".
    airline = aviation_value(
        aviation,
        "airline"
    )

    # Future/alternate mapper field.
    operator = aviation_value(
        aviation,
        "operator",
        airline
    )

    # Future/alternate mapper field.
    aircraft_type = aviation_value(
        aviation,
        "aircraft_type",
        aircraft_name
    )

    nearest_airport = aviation.get(
        "nearest_airport",
        {}
    )

    if not isinstance(
        nearest_airport,
        dict
    ):

        nearest_airport = {}

    route_context = aviation_value(
        aviation,
        "route_context"
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

        # ====================================================
        # Identity
        # ====================================================

        "icao": icao,
        "callsign": callsign,

        # ====================================================
        # Aviation enrichment
        # ====================================================

        "registration": registration,
        "country": country,
        "typecode": typecode,

        # Frontend-friendly names
        "aircraft_name": aircraft_name,
        "aircraft_type": aircraft_type,

        "airline": airline,
        "operator": operator,

        "nearest_airport": nearest_airport,
        "route_context": route_context,

        # Complete nested aviation object
        "aviation": {
            "registration": registration,
            "country": country,
            "typecode": typecode,
            "aircraft_name": aircraft_name,
            "aircraft_type": aircraft_type,
            "airline": airline,
            "operator": operator,
            "nearest_airport": nearest_airport,
            "route_context": route_context
        },

        # ====================================================
        # Position
        # ====================================================

        "latitude": latitude,
        "longitude": longitude,
        "x": x,
        "y": y,

        # ====================================================
        # Flight data
        # ====================================================

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

        # ====================================================
        # Fusion
        # ====================================================

        "risk": final_score,
        "final_score": final_score,
        "risk_level": risk_level,
        "status": risk_level,

        # ====================================================
        # Rule engine
        # ====================================================

        "rule_score": rule_score,

        "rule_reasons": aircraft.get(
            "rule_reasons",
            []
        ),

        # ====================================================
        # Machine learning
        # ====================================================

        "ml_score": ml_score,
        "ml_anomaly_score": ml_score,

        "ml_class": ml_classification,
        "ml_classification": ml_classification,

        "ml_available": ml_available,

        "ml_decision": aircraft.get(
            "ml_decision"
        ),

        "ml_prediction": aircraft.get(
            "ml_prediction"
        ),

        # ====================================================
        # Fusion indicators
        # ====================================================

        "fusion_indicators": aircraft.get(
            "fusion_indicators",
            []
        ),

        # ====================================================
        # Explanation
        # ====================================================

        "explanation": explanation,
        "anomaly_explanation": explanation,

        # ====================================================
        # Trajectory features
        # ====================================================

        "distance_from_previous_m": distance_previous,

        "time_delta_s": time_delta,

        "altitude_change_m": altitude_change,

        "speed_change_mps": speed_change,

        "heading_change_deg": heading_change,

        "calculated_speed_mps": calculated_speed,

        "acceleration_mps2": acceleration,

        # ====================================================
        # Tracker state
        # ====================================================

        "position_updated": aircraft.get(
            "position_updated",
            True
        ),

        "history_length": safe_int(
            aircraft.get(
                "history_length",
                0
            )
        ),

        # ====================================================
        # Timestamp
        # ====================================================

        "timestamp": aircraft.get(
            "timestamp"
        )
    }


# ============================================================
# BUILD COMPLETE DASHBOARD PAYLOAD
# ============================================================

def build_dashboard_payload(
    data,
    aviation_data=None
):
    """
    Convert fusion-engine JSON into the WebUI payload.

    Aviation metadata is merged from the mapper output.
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

    if not isinstance(
        aircraft_list,
        list
    ):

        aircraft_list = []

    # --------------------------------------------------------
    # Build aviation lookup
    # --------------------------------------------------------

    aviation_lookup = build_aviation_lookup(
        aviation_data
    )

    dashboard_aircraft = []

    # --------------------------------------------------------
    # Convert every fusion aircraft
    # --------------------------------------------------------

    for aircraft in aircraft_list:

        if not isinstance(
            aircraft,
            dict
        ):

            continue

        try:

            converted = convert_aircraft(
                aircraft,
                aviation_lookup
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

def send_dashboard_update(
    payload
):
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
    Continuously read fusion results and aviation
    enrichment, then update the SkyGuardian dashboard.
    """

    print()
    print("Fusion input:")
    print(FUSION_FILE)

    print()
    print("Aviation input:")
    print(AVIATION_FILE)

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
            # Read fusion data
            # ------------------------------------------------

            fusion_data = read_fusion_results()

            if fusion_data is None:

                print(
                    "[WEBUI] Waiting for fusion results...",
                    flush=True
                )

                time.sleep(
                    UPDATE_INTERVAL
                )

                continue

            # ------------------------------------------------
            # Read aviation enrichment
            # ------------------------------------------------

            aviation_data = read_aviation_data()

            # ------------------------------------------------
            # Build dashboard payload
            # ------------------------------------------------

            payload = build_dashboard_payload(
                fusion_data,
                aviation_data
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

                    risk_counts[
                        risk
                    ] += 1

            # ------------------------------------------------
            # Print when timestamp changes
            # ------------------------------------------------

            if timestamp != last_timestamp:

                print(
                    f"[WEBUI] "
                    f"Aircraft: {aircraft_count:3d} | "
                    f"Normal: {risk_counts['NORMAL']:3d} | "
                    f"Monitor: {risk_counts['MONITOR']:3d} | "
                    f"Anomaly: {risk_counts['ANOMALY']:3d} | "
                    f"Sent: {sent}",
                    flush=True
                )

                # ------------------------------------------------
                # Print aviation information for debugging
                # ------------------------------------------------

                for aircraft in payload.get(
                    "aircraft",
                    []
                ):

                    print(
                        f"[WEBUI] "
                        f"{aircraft.get('callsign', ''):<8} "
                        f"{aircraft.get('icao', '')} | "
                        f"REG="
                        f"{aircraft.get('registration', '--')} | "
                        f"TYPE="
                        f"{aircraft.get('typecode', '--')} | "
                        f"AIRLINE="
                        f"{aircraft.get('airline', '--')}",
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
        print(
            "Starting SkyGuardian..."
        )
        print()

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
