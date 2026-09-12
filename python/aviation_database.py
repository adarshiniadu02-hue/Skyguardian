import csv
import os
import sys
from functools import lru_cache

csv.field_size_limit(sys.maxsize)


BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "aviation"
)

AIRCRAFT_FILE = os.path.join(BASE_DIR, "aircraft.csv")
AIRPORTS_FILE = os.path.join(BASE_DIR, "airports.dat")
AIRLINES_FILE = os.path.join(BASE_DIR, "airlines.dat")
PLANES_FILE = os.path.join(BASE_DIR, "planes.dat")
ROUTES_FILE = os.path.join(BASE_DIR, "routes.dat")


def _clean(value):
    if value is None:
        return ""
    return str(value).strip().strip("'").strip('"')


@lru_cache(maxsize=1)
def _load_aircraft():
    data = {}

    if not os.path.exists(AIRCRAFT_FILE):
        return data

    with open(
        AIRCRAFT_FILE,
        "r",
        encoding="utf-8",
        errors="ignore",
        newline=""
    ) as f:

        reader = csv.DictReader(
            f,
            quotechar="'"
        )

        for row in reader:
            icao = _clean(
                row.get("icao24")
                or row.get("icao")
                or row.get("ICAO24")
            ).lower()

            if not icao:
                continue

            data[icao] = {
                "icao24": icao,
                "registration": _clean(row.get("registration")),
                "country": _clean(row.get("country")),
                "typecode": _clean(row.get("typecode")),
                "manufacturer": _clean(row.get("manufacturerName")),
                "model": _clean(row.get("model")),
                "operator": _clean(row.get("operator")),
                "operator_callsign": _clean(row.get("operatorCallsign")),
                "operator_icao": _clean(row.get("operatorIcao")),
                "operator_iata": _clean(row.get("operatorIata")),
                "serial_number": _clean(row.get("serialNumber")),
                "first_flight_date": _clean(row.get("firstFlightDate")),
                "status": _clean(row.get("status")),
            }

    return data


@lru_cache(maxsize=1)
def _load_airports():
    data = {}

    if not os.path.exists(AIRPORTS_FILE):
        return data

    with open(
        AIRPORTS_FILE,
        "r",
        encoding="utf-8",
        errors="ignore",
        newline=""
    ) as f:

        reader = csv.reader(f)

        for row in reader:
            if len(row) < 8:
                continue

            airport = {
                "airport_id": _clean(row[0]),
                "name": _clean(row[1]),
                "city": _clean(row[2]),
                "country": _clean(row[3]),
                "iata": _clean(row[4]).upper(),
                "icao": _clean(row[5]).upper(),
                "latitude": _clean(row[6]),
                "longitude": _clean(row[7]),
                "altitude": _clean(row[8]) if len(row) > 8 else "",
                "timezone": _clean(row[9]) if len(row) > 9 else "",
                "dst": _clean(row[10]) if len(row) > 10 else "",
                "tz_database": _clean(row[11]) if len(row) > 11 else "",
                "type": _clean(row[12]) if len(row) > 12 else "",
                "source": _clean(row[13]) if len(row) > 13 else "",
            }

            iata = airport["iata"]
            icao = airport["icao"]

            if iata and iata != r"\N":
                data[iata] = airport

            if icao and icao != r"\N":
                data[icao] = airport

    return data


@lru_cache(maxsize=1)
def _load_airlines():
    data = {}

    if not os.path.exists(AIRLINES_FILE):
        return data

    with open(
        AIRLINES_FILE,
        "r",
        encoding="utf-8",
        errors="ignore",
        newline=""
    ) as f:

        reader = csv.reader(f)

        for row in reader:
            if len(row) < 8:
                continue

            airline = {
                "airline_id": _clean(row[0]),
                "name": _clean(row[1]),
                "alias": _clean(row[2]),
                "iata": _clean(row[3]).upper(),
                "icao": _clean(row[4]).upper(),
                "callsign": _clean(row[5]),
                "country": _clean(row[6]),
                "active": _clean(row[7]),
            }

            iata = airline["iata"]
            icao = airline["icao"]

            if iata and iata != r"\N":
                data[iata] = airline

            if icao and icao != r"\N":
                data[icao] = airline

    return data


@lru_cache(maxsize=1)
def _load_planes():
    data = {}

    if not os.path.exists(PLANES_FILE):
        return data

    with open(
        PLANES_FILE,
        "r",
        encoding="utf-8",
        errors="ignore",
        newline=""
    ) as f:

        reader = csv.reader(f)

        for row in reader:
            if len(row) < 3:
                continue

            plane = {
                "name": _clean(row[0]),
                "icao": _clean(row[1]).upper(),
                "iata": _clean(row[2]).upper(),
            }

            icao = plane["icao"]
            iata = plane["iata"]

            if icao and icao != r"\N":
                data[icao] = plane

            if iata and iata != r"\N":
                data[iata] = plane

    return data


@lru_cache(maxsize=1)
def _load_routes():
    routes = []

    if not os.path.exists(ROUTES_FILE):
        return routes

    with open(
        ROUTES_FILE,
        "r",
        encoding="utf-8",
        errors="ignore",
        newline=""
    ) as f:

        reader = csv.reader(f)

        for row in reader:
            if len(row) < 9:
                continue

            routes.append({
                "airline": _clean(row[0]),
                "airline_id": _clean(row[1]),
                "source_airport": _clean(row[2]).upper(),
                "source_airport_id": _clean(row[3]),
                "destination_airport": _clean(row[4]).upper(),
                "destination_airport_id": _clean(row[5]),
                "codeshare": _clean(row[6]),
                "stops": _clean(row[7]),
                "equipment": _clean(row[8]),
            })

    return routes


def find_aircraft(icao24):
    """
    Find aircraft information using ICAO24.
    """

    icao24 = _clean(icao24).lower()

    if not icao24:
        return None

    return _load_aircraft().get(icao24)


def find_airport(code):
    """
    Find airport using IATA or ICAO code.
    """

    code = _clean(code).upper()

    if not code:
        return None

    return _load_airports().get(code)


def find_airline(code):
    """
    Find airline using IATA or ICAO code.
    """

    code = _clean(code).upper()

    if not code:
        return None

    return _load_airlines().get(code)


def find_plane(code):
    """
    Find aircraft type using ICAO or IATA aircraft code.
    """

    code = _clean(code).upper()

    if not code:
        return None

    return _load_planes().get(code)


def find_routes(source_airport=None, destination_airport=None):
    """
    Find routes involving a source and/or destination airport.
    """

    source = _clean(source_airport).upper()
    destination = _clean(destination_airport).upper()

    results = []

    for route in _load_routes():

        if source and route["source_airport"] != source:
            continue

        if destination and route["destination_airport"] != destination:
            continue

        results.append(route)

    return results


def database_status():
    """
    Return basic information about the local aviation database.
    """

    return {
        "base_dir": BASE_DIR,
        "aircraft.csv": os.path.exists(AIRCRAFT_FILE),
        "airports.dat": os.path.exists(AIRPORTS_FILE),
        "airlines.dat": os.path.exists(AIRLINES_FILE),
        "planes.dat": os.path.exists(PLANES_FILE),
        "routes.dat": os.path.exists(ROUTES_FILE),
        "aircraft_records": len(_load_aircraft()),
        "airport_records": len(_load_airports()),
        "airline_records": len(_load_airlines()),
        "plane_records": len(_load_planes()),
        "route_records": len(_load_routes()),
    }


if __name__ == "__main__":
    print("SkyGuardian Aviation Database")
    print("--------------------------------")

    status = database_status()

    for key, value in status.items():
        print(f"{key}: {value}")
