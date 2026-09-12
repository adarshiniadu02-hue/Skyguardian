#!/usr/bin/env python3

import json
import math
import time
from pathlib import Path

from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI


# ============================================================
# SKYGUARDIAN
# REALTIME FUSION → WEB DASHBOARD
# MPU → MCU BUZZER ALERTS
# ============================================================

print("=" * 70)
print("SKYGUARDIAN — EDGE AI FLIGHT MONITORING")
print("REALTIME FUSION → WEBUI → MCU BUZZER")
print("=" * 70)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FUSION_FILE = BASE_DIR / "data/live/realtime_fusion_results.json"
AVIATION_FILE = BASE_DIR / "data/live/skyguardian_aircraft.json"


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
# BUZZER SETTINGS
# ============================================================

# MCU buzzer modes:
#
# 0 = OFF
# 1 = NEW AIRCRAFT / ONE SHORT BEEP
# 2 = MONITOR / REPEATING BEEP-BEEP
# 3 = ANOMALY / FAST REPEATING BEEP

BUZZER_OFF = 0
BUZZER_NEW = 1
BUZZER_MONITOR = 2
BUZZER_ANOMALY = 3

# Last persistent buzzer mode.
last_buzzer_mode = BUZZER_OFF

# Aircraft currently known to SKYGUARDIAN.
known_aircraft = set()

# Prevents aircraft already present at startup from
# triggering NEW AIRCRAFT alarms.
aircraft_baseline_initialized = False


# ============================================================
# WEB UI
# ============================================================

ui = WebUI()


# ============================================================
# BASIC HELPERS
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


# ============================================================
# READ FUSION RESULTS
# ============================================================

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

        print(
            f"[WEBUI] Fusion read error: {e}",
            flush=True
        )

        return None


# ============================================================
# READ AVIATION DATA
# ============================================================

def read_aviation_data():
    """
    Read aviation enrichment directly from mapper output.

    Fusion does not necessarily preserve all aviation metadata,
    so this data is merged back into the dashboard using ICAO.
    """

    try:

        with open(AVIATION_FILE, "r") as f:
            data = json.load(f)

    except FileNotFoundError:

        return {}

    except json.JSONDecodeError:

        return {}

    except Exception as e:

        print(
            f"[WEBUI] Aviation read error: {e}",
            flush=True
        )

        return {}

    aircraft_list = data.get(
        "aircraft",
        []
    )

    if not isinstance(
        aircraft_list,
        list
    ):

        return {}

    aviation_lookup = {}

    for aircraft in aircraft_list:

        if not isinstance(
            aircraft,
            dict
        ):

            continue

        icao = str(
            aircraft.get(
                "icao",
                ""
            )
        ).upper().strip()

        if not icao:
            continue

        aviation_lookup[icao] = aircraft

    return aviation_lookup


# ============================================================
# BUZZER CONTROL
# ============================================================

def send_buzzer_mode(mode):
    """
    Send buzzer command to STM32 MCU through RouterBridge.

    0 = OFF
    1 = NEW AIRCRAFT
    2 = MONITOR
    3 = ANOMALY
    """

    try:

        Bridge.call(
            "set_buzzer_mode",
            int(mode)
        )

        return True

    except Exception as e:

        print(
            f"[BUZZER] Bridge error: {e}",
            flush=True
        )

        return False


def determine_persistent_buzzer_mode(aircraft_list):
    """
    Determine the persistent buzzer state.

    Priority:

        ANOMALY
        MONITOR
        NORMAL / OFF
    """

    anomaly_present = False
    monitor_present = False

    for aircraft in aircraft_list:

        if not isinstance(
            aircraft,
            dict
        ):

            continue

        risk_level = str(
            aircraft.get(
                "risk_level",
                aircraft.get(
                    "status",
                    "NORMAL"
                )
            )
        ).upper().strip()

        if risk_level == "ANOMALY":

            anomaly_present = True

        elif risk_level == "MONITOR":

            monitor_present = True

    if anomaly_present:

        return BUZZER_ANOMALY

    if monitor_present:

        return BUZZER_MONITOR

    return BUZZER_OFF


def update_buzzer(aircraft_list):
    """
    Update the physical MCU buzzer.

    NEW AIRCRAFT:
        one short beep

    MONITOR:
        repeating beep-beep

    ANOMALY:
        fast repeating alarm

    NORMAL:
        silent
    """

    global known_aircraft
    global aircraft_baseline_initialized
    global last_buzzer_mode

    # --------------------------------------------------------
    # Build current ICAO set
    # --------------------------------------------------------

    current_aircraft = set()

    for aircraft in aircraft_list:

        if not isinstance(
            aircraft,
            dict
        ):

            continue

        icao = str(
            aircraft.get(
                "icao",
                ""
            )
        ).upper().strip()

        if icao:

            current_aircraft.add(
                icao
            )

    # --------------------------------------------------------
    # First snapshot = baseline
    #
    # Aircraft already present when the application starts
    # do not trigger a NEW AIRCRAFT beep.
    # --------------------------------------------------------

    if not aircraft_baseline_initialized:

        known_aircraft = set(
            current_aircraft
        )

        aircraft_baseline_initialized = True

        persistent_mode = determine_persistent_buzzer_mode(
            aircraft_list
        )

        if persistent_mode != last_buzzer_mode:

            if send_buzzer_mode(
                persistent_mode
            ):

                last_buzzer_mode = persistent_mode

        return

    # --------------------------------------------------------
    # Detect newly appearing aircraft
    # --------------------------------------------------------

    new_aircraft = (
        current_aircraft -
        known_aircraft
    )

    # Update known aircraft.
    #
    # If an aircraft disappears and later returns,
    # it will be treated as a new detection.
    # --------------------------------------------------------

    known_aircraft = set(
        current_aircraft
    )

    # --------------------------------------------------------
    # Determine persistent alarm state
    # --------------------------------------------------------

    persistent_mode = determine_persistent_buzzer_mode(
        aircraft_list
    )

    # --------------------------------------------------------
    # NEW AIRCRAFT
    #
    # One short beep.
    # --------------------------------------------------------

    if new_aircraft:

        print(
            "[BUZZER] NEW AIRCRAFT: "
            + ", ".join(
                sorted(new_aircraft)
            ),
            flush=True
        )

        send_buzzer_mode(
            BUZZER_NEW
        )

        # Do not change last_buzzer_mode here.
        #
        # On the next update, the persistent MONITOR,
        # ANOMALY, or OFF state will be restored.

        return

    # --------------------------------------------------------
    # PERSISTENT MONITOR / ANOMALY / OFF
    #
    # Only send when the state changes.
    # --------------------------------------------------------

    if persistent_mode != last_buzzer_mode:

        if send_buzzer_mode(
            persistent_mode
        ):

            last_buzzer_mode = persistent_mode


# ============================================================
# DISTANCE / RADAR COORDINATES
# ============================================================

def calculate_xy(latitude, longitude):
    """
    Convert latitude/longitude into approximate local
    X/Y coordinates in kilometers.

    X = east/west
    Y = north/south
    """

    lat = safe_float(latitude)
    lon = safe_float(longitude)

    lat_diff = lat - RECEIVER_LAT
    lon_diff = lon - RECEIVER_LON

    km_per_lat = 111.32

    km_per_lon = (
        111.32 *
        math.cos(
            math.radians(
                RECEIVER_LAT
            )
        )
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
            * 0.3048
        )

    return safe_float(
        aircraft.get(
            "altitude",
            0
        )
    )


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
            * 0.514444
        )

    return safe_float(
        aircraft.get(
            "speed",
            0
        )
    )


# ============================================================
# BUILD DASHBOARD AIRCRAFT OBJECT
# ============================================================

def convert_aircraft(
    aircraft,
    aviation_lookup
):
    """
    Convert fusion-engine aircraft data into the format
    expected by the SkyGuardian dashboard.

    Aviation metadata is merged from skyguardian_aircraft.json.
    """

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

    altitude_m = get_altitude_m(
        aircraft
    )

    speed_mps = get_speed_mps(
        aircraft
    )

    altitude_ft = (
        altitude_m /
        0.3048
    )

    speed_kt = (
        speed_mps /
        0.514444
    )

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    icao = str(
        aircraft.get(
            "icao",
            ""
        )
    ).upper()

    callsign = aircraft.get(
        "callsign",
        ""
    )

    # --------------------------------------------------------
    # Aviation enrichment
    # --------------------------------------------------------

    aviation_source = aviation_lookup.get(
        icao,
        {}
    )

    aviation = aviation_source.get(
        "aviation",
        {}
    )

    if not isinstance(
        aviation,
        dict
    ):

        aviation = {}

    registration = aviation.get(
        "registration",
        aviation_source.get(
            "registration",
            "--"
        )
    )

    country = aviation.get(
        "country",
        aviation_source.get(
            "country",
            "--"
        )
    )

    typecode = aviation.get(
        "typecode",
        aviation_source.get(
            "typecode",
            "--"
        )
    )

    aircraft_name = aviation.get(
        "aircraft_name",
        aviation_source.get(
            "aircraft_name",
            aviation_source.get(
                "aircraft_type",
                "--"
            )
        )
    )

    airline = aviation.get(
        "airline",
        aviation_source.get(
            "airline",
            "--"
        )
    )

    operator = aviation.get(
        "operator",
        aviation_source.get(
            "operator",
            airline
        )
    )

    nearest_airport = aviation.get(
        "nearest_airport",
        aviation_source.get(
            "nearest_airport",
            {}
        )
    )

    route_context = aviation.get(
        "route_context",
        aviation_source.get(
            "route_context",
            "--"
        )
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
        ),

        # Aviation enrichment
        "registration": registration,
        "country": country,
        "typecode": typecode,
        "aircraft_name": aircraft_name,
        "aircraft_type": aircraft_name,
        "airline": airline,
        "operator": operator,
        "nearest_airport": nearest_airport,
        "route_context": route_context,

        "aviation": {
            "registration": registration,
            "country": country,
            "typecode": typecode,
            "aircraft_name": aircraft_name,
            "aircraft_type": aircraft_name,
            "airline": airline,
            "operator": operator,
            "nearest_airport": nearest_airport,
            "route_context": route_context
        }
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

    if not isinstance(
        aircraft_list,
        list
    ):

        aircraft_list = []

    aviation_lookup = read_aviation_data()

    dashboard_aircraft = []

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

def send_dashboard_update(payload):
    """
    Send latest aircraft state to frontend.
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
    Continuously read fusion results, update the WebUI,
    and control the physical MCU buzzer.
    """

    global last_buzzer_mode

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
    print("MCU buzzer:")
    print("Digital pin 8")

    print()
    print("-" * 70)
    print("Waiting for realtime fusion data...")
    print("-" * 70)

    # --------------------------------------------------------
    # Start buzzer OFF
    # --------------------------------------------------------

    if send_buzzer_mode(
        BUZZER_OFF
    ):

        last_buzzer_mode = BUZZER_OFF

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
            # Extract aircraft list
            # ------------------------------------------------

            aircraft_list = data.get(
                "aircraft",
                []
            )

            if not isinstance(
                aircraft_list,
                list
            ):

                aircraft_list = []

            # ------------------------------------------------
            # Update physical buzzer
            # ------------------------------------------------

            try:

                update_buzzer(
                    aircraft_list
                )

            except Exception as e:

                print(
                    f"[BUZZER] Update error: {e}",
                    flush=True
                )

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
            # Print aircraft state
            # ------------------------------------------------

            if timestamp != last_timestamp:

                print(
                    f"[WEBUI] Aircraft: {aircraft_count:3d} | "
                    f"Normal: {risk_counts['NORMAL']:3d} | "
                    f"Monitor: {risk_counts['MONITOR']:3d} | "
                    f"Anomaly: {risk_counts['ANOMALY']:3d} | "
                    f"Buzzer: {last_buzzer_mode} | "
                    f"Sent: {sent}",
                    flush=True
                )

                for aircraft in payload.get(
                    "aircraft",
                    []
                ):

                    print(
                        f"[WEBUI] "
                        f"{str(aircraft.get('callsign', '--')):<8} "
                        f"{str(aircraft.get('icao', '--')):<6} "
                        f"REG={str(aircraft.get('registration', '--')):<8} "
                        f"TYPE={str(aircraft.get('typecode', '--')):<5} "
                        f"AIRLINE={str(aircraft.get('airline', '--'))}",
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

            try:

                send_buzzer_mode(
                    BUZZER_OFF
                )

            except Exception:

                pass

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
