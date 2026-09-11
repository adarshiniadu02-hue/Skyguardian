#!/usr/bin/env python3

import json
import math
import time
from pathlib import Path


# ============================================================
# SKYGUARDIAN — REALTIME TRAJECTORY TRACKER
# ============================================================

INPUT_FILE = Path("data/live/skyguardian_aircraft.json")
OUTPUT_FILE = Path("data/live/realtime_trajectory.json")

UPDATE_INTERVAL = 1.0

# Number of trajectory observations retained per aircraft
MAX_HISTORY = 60

# Ignore extremely tiny movements
MIN_MOVEMENT_M = 1.0

# Ignore unrealistically small time differences
MIN_TIME_DELTA_S = 0.5

# Safety limits for calculated trajectory features
MAX_CALCULATED_SPEED_MPS = 400.0
MAX_REASONABLE_ACCELERATION_MPS2 = 15.0


# ============================================================
# STORAGE
# ============================================================

# ICAO -> list of previous observations
aircraft_history = {}

# ICAO -> last position signature
last_position_signature = {}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def haversine_distance_m(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two coordinates.

    Returns:
        Distance in meters.
    """

    R = 6371000.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2.0) ** 2
        +
        math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2.0) ** 2
    )

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def heading_difference_deg(h1, h2):
    """
    Calculate smallest angular difference between two headings.
    Result is between 0 and 180 degrees.
    """

    diff = abs(h2 - h1)

    if diff > 180.0:
        diff = 360.0 - diff

    return diff


def get_position_signature(aircraft):
    """
    Create a position signature used to detect whether
    a genuinely new position has arrived.
    """

    lat = aircraft.get("latitude")
    lon = aircraft.get("longitude")

    if lat is None or lon is None:
        return None

    return (
        round(safe_float(lat), 6),
        round(safe_float(lon), 6),
    )


def get_observation_timestamp(data, aircraft):
    """
    Estimate the actual observation time.

    readsb's snapshot timestamp represents the JSON snapshot time,
    while position_seen_sec tells us how old the position is.

    observation_time = snapshot_time - position_age
    """

    snapshot_timestamp = safe_float(
        data.get("timestamp"),
        time.time()
    )

    seen_pos = aircraft.get("position_seen_sec")

    if seen_pos is not None:
        try:
            seen_pos = float(seen_pos)

            if seen_pos >= 0:
                return snapshot_timestamp - seen_pos

        except (ValueError, TypeError):
            pass

    return snapshot_timestamp


# ============================================================
# FEATURE CALCULATION
# ============================================================

def calculate_features(previous, current):
    """
    Calculate trajectory features between two observations.
    """

    distance_m = haversine_distance_m(
        previous["latitude"],
        previous["longitude"],
        current["latitude"],
        current["longitude"],
    )

    time_delta_s = (
        current["timestamp"]
        -
        previous["timestamp"]
    )

    altitude_change_m = (
        current["altitude_m"]
        -
        previous["altitude_m"]
    )

    speed_change_mps = (
        current["speed_mps"]
        -
        previous["speed_mps"]
    )

    heading_change_deg = heading_difference_deg(
        previous["heading_deg"],
        current["heading_deg"]
    )

    # --------------------------------------------------------
    # Calculated ground speed
    # --------------------------------------------------------

    if time_delta_s >= MIN_TIME_DELTA_S:

        calculated_speed_mps = (
            distance_m / time_delta_s
        )

    else:

        calculated_speed_mps = 0.0

    # --------------------------------------------------------
    # Acceleration
    # --------------------------------------------------------

    if time_delta_s >= MIN_TIME_DELTA_S:

        acceleration_mps2 = (
            speed_change_mps / time_delta_s
        )

    else:

        acceleration_mps2 = 0.0

    # --------------------------------------------------------
    # Safety limits
    # --------------------------------------------------------

    if calculated_speed_mps > MAX_CALCULATED_SPEED_MPS:

        calculated_speed_mps = MAX_CALCULATED_SPEED_MPS

    if abs(acceleration_mps2) > MAX_REASONABLE_ACCELERATION_MPS2:

        acceleration_mps2 = (
            math.copysign(
                MAX_REASONABLE_ACCELERATION_MPS2,
                acceleration_mps2
            )
        )

    return {
        "distance_from_previous_m": round(
            distance_m,
            3
        ),

        "time_delta_s": round(
            time_delta_s,
            3
        ),

        "altitude_change_m": round(
            altitude_change_m,
            3
        ),

        "speed_change_mps": round(
            speed_change_mps,
            3
        ),

        "heading_change_deg": round(
            heading_change_deg,
            3
        ),

        "calculated_speed_mps": round(
            calculated_speed_mps,
            3
        ),

        "acceleration_mps2": round(
            acceleration_mps2,
            3
        ),
    }


# ============================================================
# PROCESS ONE AIRCRAFT
# ============================================================

def process_aircraft(data, aircraft):
    """
    Process one aircraft and generate its latest trajectory
    observation and features.
    """

    icao = aircraft.get("icao")

    if not icao:
        return None, False

    latitude = aircraft.get("latitude")
    longitude = aircraft.get("longitude")

    if latitude is None or longitude is None:
        return None, False

    latitude = safe_float(latitude)
    longitude = safe_float(longitude)

    altitude_ft = safe_float(
        aircraft.get("altitude_ft"),
        0.0
    )

    speed_kt = safe_float(
        aircraft.get("speed_kt"),
        0.0
    )

    heading_deg = safe_float(
        aircraft.get("heading_deg"),
        0.0
    )

    vertical_rate_fpm = safe_float(
        aircraft.get("vertical_rate_fpm"),
        0.0
    )

    # Convert knots -> m/s
    speed_mps = speed_kt * 0.514444

    # Convert feet -> meters
    altitude_m = altitude_ft * 0.3048

    observation_timestamp = get_observation_timestamp(
        data,
        aircraft
    )

    # --------------------------------------------------------
    # Detect duplicate position
    # --------------------------------------------------------

    position_signature = get_position_signature(
        aircraft
    )

    previous_signature = last_position_signature.get(
        icao
    )

    position_updated = (
        position_signature is not None
        and
        position_signature != previous_signature
    )

    # If this is not a new position, return current state
    if not position_updated:

        history = aircraft_history.get(
            icao,
            []
        )

        latest = history[-1] if history else None

        result = {
            "icao": icao,

            "callsign": aircraft.get(
                "callsign",
                ""
            ),

            "latitude": latitude,
            "longitude": longitude,

            "altitude_ft": altitude_ft,
            "geometric_altitude_ft": aircraft.get(
                "geometric_altitude_ft"
            ),

            "speed_kt": speed_kt,

            "heading_deg": heading_deg,

            "vertical_rate_fpm": vertical_rate_fpm,

            "distance_nm": aircraft.get(
                "distance_nm"
            ),

            "direction_deg": aircraft.get(
                "direction_deg"
            ),

            "seen_sec": aircraft.get(
                "seen_sec"
            ),

            "position_seen_sec": aircraft.get(
                "position_seen_sec"
            ),

            "rssi_db": aircraft.get(
                "rssi_db"
            ),

            "timestamp": observation_timestamp,

            "position_updated": False,

            "history_length": len(history),

            # Keep latest features available
            "distance_from_previous_m": (
                latest.get(
                    "distance_from_previous_m",
                    0.0
                )
                if latest else 0.0
            ),

            "time_delta_s": (
                latest.get(
                    "time_delta_s",
                    0.0
                )
                if latest else 0.0
            ),

            "altitude_change_m": (
                latest.get(
                    "altitude_change_m",
                    0.0
                )
                if latest else 0.0
            ),

            "speed_change_mps": (
                latest.get(
                    "speed_change_mps",
                    0.0
                )
                if latest else 0.0
            ),

            "heading_change_deg": (
                latest.get(
                    "heading_change_deg",
                    0.0
                )
                if latest else 0.0
            ),

            "calculated_speed_mps": (
                latest.get(
                    "calculated_speed_mps",
                    0.0
                )
                if latest else 0.0
            ),

            "acceleration_mps2": (
                latest.get(
                    "acceleration_mps2",
                    0.0
                )
                if latest else 0.0
            ),
        }

        return result, False

    # --------------------------------------------------------
    # Create current observation
    # --------------------------------------------------------

    current = {
        "timestamp": observation_timestamp,

        "latitude": latitude,

        "longitude": longitude,

        "altitude_m": altitude_m,

        "speed_mps": speed_mps,

        "heading_deg": heading_deg,

        "vertical_rate_fpm": vertical_rate_fpm,
    }

    history = aircraft_history.setdefault(
        icao,
        []
    )

    # --------------------------------------------------------
    # Calculate trajectory features
    # --------------------------------------------------------

    if history:

        previous = history[-1]

        features = calculate_features(
            previous,
            current
        )

    else:

        features = {
            "distance_from_previous_m": 0.0,
            "time_delta_s": 0.0,
            "altitude_change_m": 0.0,
            "speed_change_mps": 0.0,
            "heading_change_deg": 0.0,
            "calculated_speed_mps": 0.0,
            "acceleration_mps2": 0.0,
        }

    # --------------------------------------------------------
    # Ignore extremely tiny movement
    # --------------------------------------------------------

    if (
        features["distance_from_previous_m"]
        < MIN_MOVEMENT_M
        and
        len(history) > 0
    ):

        position_updated = False

        result = {
            "icao": icao,
            "callsign": aircraft.get(
                "callsign",
                ""
            ),
            "latitude": latitude,
            "longitude": longitude,
            "altitude_ft": altitude_ft,
            "geometric_altitude_ft": aircraft.get(
                "geometric_altitude_ft"
            ),
            "speed_kt": speed_kt,
            "heading_deg": heading_deg,
            "vertical_rate_fpm": vertical_rate_fpm,
            "distance_nm": aircraft.get(
                "distance_nm"
            ),
            "direction_deg": aircraft.get(
                "direction_deg"
            ),
            "seen_sec": aircraft.get(
                "seen_sec"
            ),
            "position_seen_sec": aircraft.get(
                "position_seen_sec"
            ),
            "rssi_db": aircraft.get(
                "rssi_db"
            ),
            "timestamp": observation_timestamp,
            "position_updated": False,
            "history_length": len(history),

            **features,
        }

        return result, False

    # --------------------------------------------------------
    # Add new observation to history
    # --------------------------------------------------------

    history.append(
        {
            **current,
            **features,
        }
    )

    # Keep only latest MAX_HISTORY observations
    if len(history) > MAX_HISTORY:

        aircraft_history[icao] = history[
            -MAX_HISTORY:
        ]

    # Update position signature
    last_position_signature[
        icao
    ] = position_signature

    # --------------------------------------------------------
    # Create output record
    # --------------------------------------------------------

    result = {
        "icao": icao,

        "callsign": aircraft.get(
            "callsign",
            ""
        ),

        "latitude": latitude,

        "longitude": longitude,

        "altitude_ft": altitude_ft,

        "geometric_altitude_ft": aircraft.get(
            "geometric_altitude_ft"
        ),

        "speed_kt": speed_kt,

        "heading_deg": heading_deg,

        "vertical_rate_fpm": vertical_rate_fpm,

        "distance_nm": aircraft.get(
            "distance_nm"
        ),

        "direction_deg": aircraft.get(
            "direction_deg"
        ),

        "seen_sec": aircraft.get(
            "seen_sec"
        ),

        "position_seen_sec": aircraft.get(
            "position_seen_sec"
        ),

        "rssi_db": aircraft.get(
            "rssi_db"
        ),

        "timestamp": observation_timestamp,

        "position_updated": True,

        "history_length": len(
            aircraft_history[icao]
        ),

        **features,
    }

    return result, True


# ============================================================
# READ INPUT
# ============================================================

def read_input():

    try:

        with open(
            INPUT_FILE,
            "r"
        ) as f:

            return json.load(f)

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return None


# ============================================================
# WRITE OUTPUT
# ============================================================

def write_output(result):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = OUTPUT_FILE.with_suffix(
        ".tmp"
    )

    with open(
        temporary_file,
        "w"
    ) as f:

        json.dump(
            result,
            f,
            indent=2
        )

    temporary_file.replace(
        OUTPUT_FILE
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("SKYGUARDIAN — REALTIME TRAJECTORY TRACKER")
    print("=" * 72)

    print(
        f"Input   : {INPUT_FILE}"
    )

    print(
        f"Output  : {OUTPUT_FILE}"
    )

    print(
        f"Update  : {UPDATE_INTERVAL}s"
    )

    print(
        f"History : {MAX_HISTORY} observations"
    )

    print(
        f"Min movement : {MIN_MOVEMENT_M} m"
    )

    print(
        f"Max calculated speed : "
        f"{MAX_CALCULATED_SPEED_MPS} m/s"
    )

    print("-" * 72)

    while True:

        loop_start = time.time()

        data = read_input()

        if data is None:

            print(
                "Waiting for aircraft data..."
            )

            time.sleep(
                UPDATE_INTERVAL
            )

            continue

        current_aircraft = data.get(
            "aircraft",
            []
        )

        processed_aircraft = []

        position_updates = 0

        for aircraft in current_aircraft:

            result, updated = process_aircraft(
                data,
                aircraft
            )

            if result is None:
                continue

            processed_aircraft.append(
                result
            )

            if updated:
                position_updates += 1

        # ----------------------------------------------------
        # Create output
        # ----------------------------------------------------

        output = {
            "timestamp": data.get(
                "timestamp",
                time.time()
            ),

            "aircraft_count": len(
                processed_aircraft
            ),

            "position_updates": position_updates,

            "aircraft": processed_aircraft,
        }

        write_output(
            output
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Print every update on a NEW LINE.
        # ----------------------------------------------------

        print(
            f"Aircraft: {len(processed_aircraft):3d} | "
            f"Position updates: {position_updates:3d} | "
            f"Timestamp: {output['timestamp']}",
            flush=True
        )

        # ----------------------------------------------------
        # Maintain approximately 1-second update interval
        # ----------------------------------------------------

        elapsed = time.time() - loop_start

        sleep_time = max(
            0.0,
            UPDATE_INTERVAL - elapsed
        )

        time.sleep(
            sleep_time
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n\nSkyGuardian trajectory tracker stopped."
        )
