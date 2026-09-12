#!/usr/bin/env python3

"""
============================================================
SkyGuardian OpenSky Loader
============================================================

Loads historical OpenSky state-vector CSV data.

Input:
    data/raw/states_2018-05-28-00.csv

Required fields:
    time
    icao24
    lat
    lon

Optional fields:
    velocity
    heading
    vertrate
    callsign
    onground
    squawk
    baroaltitude
    geoaltitude
    lastposupdate
    lastcontact

The loader is intentionally tolerant of missing optional
values because OpenSky datasets can contain incomplete
state vectors.

All geographic filtering is performed here.

SkyGuardian regional monitoring region:
    Latitude  : 47.0 to 55.0
    Longitude : 5.0 to 15.0
============================================================
"""

import csv
import os
from pathlib import Path


# ============================================================
# DEFAULT CONFIGURATION
# ============================================================

DEFAULT_LAT_MIN = 47.0
DEFAULT_LAT_MAX = 55.0

DEFAULT_LON_MIN = 5.0
DEFAULT_LON_MAX = 15.0


# ============================================================
# UNIT CONVERSION
# ============================================================

MPS_TO_KNOTS = 1.943844492

METERS_TO_FEET = 3.280839895


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "states_2018-05-28-00.csv"
)


# ============================================================
# OPENSKY LOADER
# ============================================================

class OpenSkyLoader:

    def __init__(
        self,
        dataset_path=None,
        lat_min=DEFAULT_LAT_MIN,
        lat_max=DEFAULT_LAT_MAX,
        lon_min=DEFAULT_LON_MIN,
        lon_max=DEFAULT_LON_MAX
    ):

        # ----------------------------------------------------
        # Dataset
        # ----------------------------------------------------

        if dataset_path is None:
            dataset_path = DEFAULT_DATASET

        self.dataset_path = Path(dataset_path).expanduser().resolve()

        # ----------------------------------------------------
        # Monitoring region
        # ----------------------------------------------------

        self.lat_min = float(lat_min)
        self.lat_max = float(lat_max)

        self.lon_min = float(lon_min)
        self.lon_max = float(lon_max)

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        self.observations = []

        self.aircraft = {}

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        self.rows_scanned = 0
        self.valid_rows = 0
        self.invalid_rows = 0
        self.regional_rows = 0

    # ========================================================
    # SAFE FLOAT
    # ========================================================

    @staticmethod
    def safe_float(value):

        if value is None:
            return None

        value = str(value).strip()

        if value == "":
            return None

        try:
            number = float(value)

            # Reject NaN / infinity
            if number != number:
                return None

            if number in (float("inf"), float("-inf")):
                return None

            return number

        except (ValueError, TypeError):

            return None

    # ========================================================
    # SAFE INT
    # ========================================================

    @staticmethod
    def safe_int(value):

        if value is None:
            return None

        value = str(value).strip()

        if value == "":
            return None

        try:
            return int(value)

        except (ValueError, TypeError):

            return None

    # ========================================================
    # SAFE BOOLEAN
    # ========================================================

    @staticmethod
    def safe_bool(value):

        if value is None:
            return None

        value = str(value).strip().lower()

        if value in ("true", "1", "yes"):
            return True

        if value in ("false", "0", "no"):
            return False

        return None

    # ========================================================
    # CHECK REGION
    # ========================================================

    def inside_region(self, latitude, longitude):

        if latitude is None or longitude is None:
            return False

        return (
            self.lat_min <= latitude <= self.lat_max
            and
            self.lon_min <= longitude <= self.lon_max
        )

    # ========================================================
    # NORMALIZE ROW
    # ========================================================

    def normalize_row(self, row):

        # ----------------------------------------------------
        # ICAO
        # ----------------------------------------------------

        icao = str(
            row.get("icao24", "")
        ).strip().upper()

        if not icao:
            return None

        # ----------------------------------------------------
        # Mandatory position
        # ----------------------------------------------------

        timestamp = self.safe_float(
            row.get("time")
        )

        latitude = self.safe_float(
            row.get("lat")
        )

        longitude = self.safe_float(
            row.get("lon")
        )

        # ----------------------------------------------------
        # Position is mandatory
        # ----------------------------------------------------

        if timestamp is None:
            return None

        if latitude is None:
            return None

        if longitude is None:
            return None

        # ----------------------------------------------------
        # Basic geographic validation
        # ----------------------------------------------------

        if not (-90.0 <= latitude <= 90.0):
            return None

        if not (-180.0 <= longitude <= 180.0):
            return None

        # ----------------------------------------------------
        # Optional values
        # ----------------------------------------------------

        velocity_mps = self.safe_float(
            row.get("velocity")
        )

        heading = self.safe_float(
            row.get("heading")
        )

        vertical_rate_mps = self.safe_float(
            row.get("vertrate")
        )

        baroaltitude_m = self.safe_float(
            row.get("baroaltitude")
        )

        geoaltitude_m = self.safe_float(
            row.get("geoaltitude")
        )

        # ----------------------------------------------------
        # Unit conversion
        #
        # OpenSky:
        # velocity     = m/s
        # vertrate     = m/s
        # altitude     = meters
        #
        # SkyGuardian:
        # speed        = knots
        # vertical_rate = ft/min approximately
        # altitude     = feet
        # ----------------------------------------------------

        speed_knots = None

        if velocity_mps is not None:
            speed_knots = velocity_mps * MPS_TO_KNOTS

        altitude_ft = None

        if baroaltitude_m is not None:
            altitude_ft = (
                baroaltitude_m
                * METERS_TO_FEET
            )

        geoaltitude_ft = None

        if geoaltitude_m is not None:
            geoaltitude_ft = (
                geoaltitude_m
                * METERS_TO_FEET
            )

        vertical_rate_fpm = None

        if vertical_rate_mps is not None:
            vertical_rate_fpm = (
                vertical_rate_mps
                * METERS_TO_FEET
                * 60.0
            )

        # ----------------------------------------------------
        # Callsign
        # ----------------------------------------------------

        callsign = str(
            row.get("callsign", "")
        ).strip()

        if callsign == "":
            callsign = None

        # ----------------------------------------------------
        # Normalize heading
        # ----------------------------------------------------

        if heading is not None:

            heading %= 360.0

        # ----------------------------------------------------
        # Build normalized observation
        # ----------------------------------------------------

        observation = {

            "icao": icao,

            "timestamp": timestamp,

            "latitude": latitude,

            "longitude": longitude,

            "speed": speed_knots,

            "speed_mps": velocity_mps,

            "heading": heading,

            "vertical_rate": vertical_rate_fpm,

            "vertical_rate_mps": vertical_rate_mps,

            "altitude": altitude_ft,

            "altitude_m": baroaltitude_m,

            "geoaltitude": geoaltitude_ft,

            "geoaltitude_m": geoaltitude_m,

            "callsign": callsign,

            "onground": self.safe_bool(
                row.get("onground")
            ),

            "alert": self.safe_bool(
                row.get("alert")
            ),

            "spi": self.safe_bool(
                row.get("spi")
            ),

            "squawk": self.safe_int(
                row.get("squawk")
            ),

            "lastposupdate": self.safe_float(
                row.get("lastposupdate")
            ),

            "lastcontact": self.safe_float(
                row.get("lastcontact")
            ),

            "source": "OPENSKY",

            "mode": "HISTORICAL"
        }

        return observation

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load(self, limit=None):

        # ----------------------------------------------------
        # Reset previous results
        # ----------------------------------------------------

        self.observations = []

        self.aircraft = {}

        self.rows_scanned = 0
        self.valid_rows = 0
        self.invalid_rows = 0
        self.regional_rows = 0

        # ----------------------------------------------------
        # Check file
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("SKYGUARDIAN OPEN SKY LOADER")
        print("=" * 60)

        print()
        print("Project root:")
        print(PROJECT_ROOT)

        print()
        print("Dataset:")
        print(self.dataset_path)

        if not self.dataset_path.exists():

            print()
            print("ERROR: OpenSky CSV not found")
            print(self.dataset_path)

            return []

        print()
        print("OpenSky CSV FOUND")

        try:

            file_size = (
                self.dataset_path.stat().st_size
            )

            print(
                "File size:",
                file_size,
                "bytes"
            )

        except OSError:

            pass

        # ----------------------------------------------------
        # Open CSV
        # ----------------------------------------------------

        try:

            with open(
                self.dataset_path,
                "r",
                encoding="utf-8",
                newline=""
            ) as file:

                reader = csv.DictReader(file)

                # ------------------------------------------------
                # Check columns
                # ------------------------------------------------

                columns = reader.fieldnames or []

                print()
                print("CSV columns detected:")

                print(
                    ", ".join(columns)
                )

                required_columns = {
                    "time",
                    "icao24",
                    "lat",
                    "lon"
                }

                missing = (
                    required_columns
                    - set(columns)
                )

                if missing:

                    print()
                    print(
                        "ERROR: Required columns missing:"
                    )

                    print(
                        ", ".join(
                            sorted(missing)
                        )
                    )

                    return []

                # ------------------------------------------------
                # Read rows
                # ------------------------------------------------

                for row in reader:

                    self.rows_scanned += 1

                    # ------------------------------------------------
                    # Optional limit
                    # ------------------------------------------------

                    if (
                        limit is not None
                        and
                        len(self.observations) >= limit
                    ):
                        break

                    # ------------------------------------------------
                    # Normalize
                    # ------------------------------------------------

                    observation = (
                        self.normalize_row(row)
                    )

                    if observation is None:

                        self.invalid_rows += 1

                        continue

                    self.valid_rows += 1

                    # ------------------------------------------------
                    # Regional filter
                    # ------------------------------------------------

                    if not self.inside_region(
                        observation["latitude"],
                        observation["longitude"]
                    ):

                        continue

                    # ------------------------------------------------
                    # Regional observation
                    # ------------------------------------------------

                    self.regional_rows += 1

                    self.observations.append(
                        observation
                    )

                    # ------------------------------------------------
                    # Store aircraft
                    #
                    # Latest observation wins.
                    # ------------------------------------------------

                    icao = observation["icao"]

                    self.aircraft[icao] = (
                        observation
                    )

        except Exception as error:

            print()
            print("ERROR while reading OpenSky CSV:")
            print(error)

            return []

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("OPEN SKY LOAD RESULT")
        print("=" * 60)

        print()
        print(
            "CSV rows scanned:",
            self.rows_scanned
        )

        print(
            "Valid observations:",
            self.valid_rows
        )

        print(
            "Invalid/skipped rows:",
            self.invalid_rows
        )

        print(
            "Regional observations:",
            self.regional_rows
        )

        print(
            "Aircraft observations loaded:",
            len(self.observations)
        )

        print(
            "Unique aircraft:",
            len(self.aircraft)
        )

        if len(self.observations) == 0:

            print()
            print(
                "WARNING: No aircraft observations "
                "were loaded."
            )

        else:

            print()
            print(
                "Example normalized aircraft:"
            )

            print("-" * 60)

            example = self.observations[0]

            for key in [
                "icao",
                "timestamp",
                "latitude",
                "longitude",
                "speed",
                "heading",
                "vertical_rate",
                "altitude",
                "geoaltitude",
                "callsign",
                "onground",
                "squawk",
                "source",
                "mode"
            ]:

                print(
                    f"{key:<16}:",
                    example.get(key)
                )

        print()
        print("=" * 60)

        return self.observations

    # ========================================================
    # ALIASES
    # ========================================================

    def load_observations(self, limit=None):

        return self.load(limit=limit)

    # ========================================================

    def get_observations(self):

        return self.observations

    # ========================================================

    def get_aircraft(self):

        return self.aircraft

    # ========================================================

    def get_unique_aircraft(self):

        return self.aircraft

    # ========================================================
    # GET AIRCRAFT LIST
    # ========================================================

    def get_aircraft_list(self):

        return list(
            self.aircraft.values()
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    def get_statistics(self):

        return {

            "rows_scanned":
                self.rows_scanned,

            "valid_rows":
                self.valid_rows,

            "invalid_rows":
                self.invalid_rows,

            "regional_rows":
                self.regional_rows,

            "aircraft_observations":
                len(self.observations),

            "unique_aircraft":
                len(self.aircraft)
        }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("Running OpenSky loader test...")

    loader = OpenSkyLoader()

    observations = loader.load()

    print()
    print("=" * 60)

    print(
        "Total observations returned:",
        len(observations)
    )

    print()

    print(
        "Unique aircraft returned:",
        len(loader.get_unique_aircraft())
    )

    print()

    # --------------------------------------------------------
    # Show first five aircraft
    # --------------------------------------------------------

    aircraft_list = (
        loader.get_aircraft_list()
    )

    if aircraft_list:

        print(
            "First aircraft records:"
        )

        print("-" * 60)

        for aircraft in aircraft_list[:5]:

            print(
                aircraft["icao"],
                "|",
                aircraft.get("callsign"),
                "|",
                aircraft["latitude"],
                "|",
                aircraft["longitude"],
                "|",
                aircraft.get("altitude"),
                "ft"
            )

    print()
    print(
        "OpenSky loader test complete."
    )