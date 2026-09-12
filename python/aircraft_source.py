import csv
import os


# ============================================================
# SKYGUARDIAN
# AIRCRAFT DATA SOURCE
#
# OpenSky historical CSV -> normalized aircraft objects
# ============================================================


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)


# ============================================================
# DATASET
# ============================================================

CSV_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "raw",
    "states_2018-05-28-00.csv"
)


# ============================================================
# REGION
#
# Germany / Central Europe
# ============================================================

LAT_MIN = 47.0
LAT_MAX = 55.0

LON_MIN = 5.0
LON_MAX = 15.0


# ============================================================
# NUMBER OF AIRCRAFT SENT TO DASHBOARD
# ============================================================

MAX_AIRCRAFT = 10


# ============================================================
# CACHE
# ============================================================

_aircraft_cache = None


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value):

    try:

        if value is None:
            return None

        value = str(value).strip()

        if value == "":
            return None

        return float(value)

    except (ValueError, TypeError):

        return None


# ============================================================
# LAT/LON -> RADAR COORDINATES
#
# Returns percentage values:
#
# x = 5 ... 95
# y = 5 ... 95
# ============================================================

def latlon_to_radar(latitude, longitude):

    if latitude is None or longitude is None:

        return 50.0, 50.0


    x = (
        (longitude - LON_MIN)
        /
        (LON_MAX - LON_MIN)
    ) * 90.0 + 5.0


    y = (
        (LAT_MAX - latitude)
        /
        (LAT_MAX - LAT_MIN)
    ) * 90.0 + 5.0


    x = max(5.0, min(95.0, x))

    y = max(5.0, min(95.0, y))


    return x, y


# ============================================================
# NORMALIZE ONE CSV ROW
# ============================================================

def normalize_row(row):

    # --------------------------------------------------------
    # ICAO
    # --------------------------------------------------------

    icao = (
        row.get("icao24")
        or ""
    ).strip().upper()


    if not icao:

        return None


    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    latitude = safe_float(
        row.get("lat")
    )

    longitude = safe_float(
        row.get("lon")
    )


    if latitude is None or longitude is None:

        return None


    # --------------------------------------------------------
    # REGION FILTER
    # --------------------------------------------------------

    if latitude < LAT_MIN:
        return None

    if latitude > LAT_MAX:
        return None

    if longitude < LON_MIN:
        return None

    if longitude > LON_MAX:
        return None


    # --------------------------------------------------------
    # RAW VALUES
    #
    # IMPORTANT:
    #
    # Keep OpenSky units here.
    #
    # velocity    = m/s
    # altitude    = meters
    # vertrate    = m/s
    #
    # main.py will convert them for display.
    # --------------------------------------------------------

    timestamp = safe_float(
        row.get("time")
    )

    velocity = safe_float(
        row.get("velocity")
    )

    heading = safe_float(
        row.get("heading")
    )

    vertical_rate = safe_float(
        row.get("vertrate")
    )

    altitude = safe_float(
        row.get("baroaltitude")
    )

    geoaltitude = safe_float(
        row.get("geoaltitude")
    )


    # --------------------------------------------------------
    # CALLSIGN
    # --------------------------------------------------------

    callsign = (
        row.get("callsign")
        or ""
    ).strip()


    if not callsign:

        callsign = icao


    # --------------------------------------------------------
    # MISSING NUMERIC VALUES
    # --------------------------------------------------------

    if velocity is None:
        velocity = 0.0

    if heading is None:
        heading = 0.0

    if vertical_rate is None:
        vertical_rate = 0.0

    if altitude is None:
        altitude = 0.0

    if geoaltitude is None:
        geoaltitude = altitude


    # --------------------------------------------------------
    # RADAR POSITION
    # --------------------------------------------------------

    x, y = latlon_to_radar(
        latitude,
        longitude
    )


    # --------------------------------------------------------
    # BASIC STATUS
    #
    # NO AI YET.
    # --------------------------------------------------------

    status = "NORMAL"

    risk = 0


    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {

        "icao": icao,

        "callsign": callsign,

        "timestamp": timestamp,

        "latitude": latitude,

        "longitude": longitude,

        # OpenSky raw units
        "altitude": altitude,

        "geoaltitude": geoaltitude,

        "speed": velocity,

        "heading": heading,

        "vertical_rate": vertical_rate,

        # Radar
        "x": x,

        "y": y,

        # Analysis
        "status": status,

        "risk": risk,

        # Source information
        "source": "OPENSKY",

        "mode": "HISTORICAL"

    }


# ============================================================
# LOAD OPENSKY DATA
# ============================================================

def load_opensky():

    global _aircraft_cache


    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    if _aircraft_cache is not None:

        return _aircraft_cache


    print()
    print("=" * 60)
    print("SKYGUARDIAN OPEN SKY DATA SOURCE")
    print("=" * 60)

    print()
    print("Project root:")
    print(PROJECT_ROOT)

    print()
    print("CSV:")
    print(CSV_FILE)


    # --------------------------------------------------------
    # FILE CHECK
    # --------------------------------------------------------

    if not os.path.isfile(CSV_FILE):

        print()
        print("ERROR: OpenSky CSV NOT FOUND")
        print(CSV_FILE)
        print()

        _aircraft_cache = []

        return _aircraft_cache


    print()
    print(
        "OpenSky CSV FOUND:",
        os.path.getsize(CSV_FILE),
        "bytes"
    )


    # --------------------------------------------------------
    # LATEST ROW FOR EACH AIRCRAFT
    # --------------------------------------------------------

    latest = {}


    rows_scanned = 0

    valid_rows = 0

    regional_rows = 0

    skipped_rows = 0


    print()
    print("Scanning OpenSky dataset...")
    print()


    # --------------------------------------------------------
    # READ CSV
    # --------------------------------------------------------

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)


        if not reader.fieldnames:

            print("ERROR: CSV has no header")

            _aircraft_cache = []

            return _aircraft_cache


        print(
            "CSV columns:",
            ", ".join(reader.fieldnames)
        )


        # ----------------------------------------------------
        # PROCESS ROWS
        # ----------------------------------------------------

        for row in reader:

            rows_scanned += 1


            icao = (
                row.get("icao24")
                or ""
            ).strip().upper()


            if not icao:

                skipped_rows += 1

                continue


            latitude = safe_float(
                row.get("lat")
            )

            longitude = safe_float(
                row.get("lon")
            )


            if latitude is None or longitude is None:

                skipped_rows += 1

                continue


            valid_rows += 1


            # -----------------------------------------------
            # REGION
            # -----------------------------------------------

            if latitude < LAT_MIN:
                continue

            if latitude > LAT_MAX:
                continue

            if longitude < LON_MIN:
                continue

            if longitude > LON_MAX:
                continue


            regional_rows += 1


            timestamp = safe_float(
                row.get("time")
            )


            # -----------------------------------------------
            # Keep latest observation
            # -----------------------------------------------

            previous = latest.get(
                icao
            )


            if previous is None:

                latest[icao] = row

            else:

                old_time = safe_float(
                    previous.get("time")
                )


                if timestamp is None:

                    continue


                if old_time is None:

                    latest[icao] = row

                elif timestamp >= old_time:

                    latest[icao] = row


    # ========================================================
    # STATISTICS
    # ========================================================

    print()
    print("=" * 60)
    print("OPEN SKY SCAN RESULT")
    print("=" * 60)

    print(
        "Rows scanned:",
        rows_scanned
    )

    print(
        "Valid rows:",
        valid_rows
    )

    print(
        "Skipped rows:",
        skipped_rows
    )

    print(
        "Regional observations:",
        regional_rows
    )

    print(
        "Unique regional aircraft:",
        len(latest)
    )


    # ========================================================
    # NORMALIZE
    # ========================================================

    normalized = []


    for icao, row in latest.items():

        aircraft = normalize_row(
            row
        )


        if aircraft is not None:

            normalized.append(
                aircraft
            )


    # ========================================================
    # SORT
    # ========================================================

    normalized.sort(
        key=lambda aircraft:
            aircraft.get(
                "timestamp"
            ) or 0,
        reverse=True
    )


    # ========================================================
    # LIMIT
    # ========================================================

    _aircraft_cache = normalized[
        :MAX_AIRCRAFT
    ]


    # ========================================================
    # PRINT AIRCRAFT
    # ========================================================

    print()
    print("=" * 60)
    print("AIRCRAFT SENT TO DASHBOARD")
    print("=" * 60)

    print(
        "Aircraft:",
        len(_aircraft_cache)
    )

    print()


    for index, aircraft in enumerate(
        _aircraft_cache,
        start=1
    ):

        print(
            f"{index:02d}. "
            f"{aircraft['icao']} | "
            f"{aircraft['callsign']} | "
            f"LAT {aircraft['latitude']:.4f} | "
            f"LON {aircraft['longitude']:.4f} | "
            f"ALT {aircraft['altitude']:.1f} m | "
            f"SPEED {aircraft['speed']:.1f} m/s"
        )


    print()
    print("=" * 60)
    print()


    return _aircraft_cache


# ============================================================
# PUBLIC API
# ============================================================

def get_aircraft():

    return load_opensky()


# ============================================================
# RESET
# ============================================================

def reset_cache():

    global _aircraft_cache

    _aircraft_cache = None


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("Running aircraft_source.py test...")
    print()

    aircraft = get_aircraft()

    print()
    print(
        "Returned aircraft:",
        len(aircraft)
    )

    if aircraft:

        print()
        print("FIRST AIRCRAFT")
        print("-" * 40)
        print(aircraft[0])

    else:

        print()
        print("NO AIRCRAFT RETURNED")