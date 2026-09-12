#!/usr/bin/env python3
import csv
import json
import math
import time
from pathlib import Path

INPUT_FILE = Path("data/live/aircraft.json")
OUTPUT_FILE = Path("data/live/skyguardian_aircraft.json")

AVIATION_DIR = Path("data/aviation")
AIRCRAFT_DB = AVIATION_DIR / "aircraft.csv"
AIRPORTS_DB = AVIATION_DIR / "airports.dat"
AIRLINES_DB = AVIATION_DIR / "airlines.dat"
PLANES_DB = AVIATION_DIR / "planes.dat"
ROUTES_DB = AVIATION_DIR / "routes.dat"

RECEIVER_LAT = 52.108889
RECEIVER_LON = 11.615278
MAX_SEEN_SECONDS = 5.0

_db = {"aircraft": {}, "airports": [], "airlines": {}, "planes": {}, "routes": {}}
_loaded = False


def clean(v):
    return str(v or "").strip()


def safe_float(v):
    try:
        if v in (None, "", "\\N"):
            return None
        return float(v)
    except (ValueError, TypeError):
        return None


def load_openflights(path):
    rows = []
    if not path.exists():
        print("DB missing:", path)
        return rows

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = [x.strip().strip('"') for x in line.split(",")]
            rows.append(parts)
    return rows


def load_databases():
    global _loaded
    if _loaded:
        return

    # OpenSky aircraft database: load flexibly by header.
    if AIRCRAFT_DB.exists():
        try:
            with open(AIRCRAFT_DB, encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    icao = clean(row.get("icao24") or row.get("icao") or row.get("icao24_hex")).upper()
                    if icao:
                        _db["aircraft"][icao] = {
                            "registration": clean(row.get("registration")),
                            "country": clean(row.get("country") or row.get("country_name")),
                            "typecode": clean(row.get("typecode") or row.get("type_code")),
                        }
        except Exception as e:
            print("Aircraft DB load error:", e)

    # OpenFlights airports.dat
    for p in load_openflights(AIRPORTS_DB):
        if len(p) < 8:
            continue
        _db["airports"].append({
            "name": clean(p[1]),
            "city": clean(p[2]),
            "country": clean(p[3]),
            "iata": clean(p[4]),
            "icao": clean(p[5]),
            "lat": safe_float(p[6]),
            "lon": safe_float(p[7]),
        })

    # OpenFlights airlines.dat
    for p in load_openflights(AIRLINES_DB):
        if len(p) < 7:
            continue
        icao = clean(p[5]).upper()
        iata = clean(p[3]).upper()
        item = {
            "name": clean(p[1]),
            "iata": iata,
            "icao": icao,
            "callsign": clean(p[6]),
            "country": clean(p[6]) if False else clean(p[6]),
        }
        if icao:
            _db["airlines"][icao] = item
        if iata:
            _db["airlines"][iata] = item

    # OpenFlights planes.dat: name, IATA, ICAO
    for p in load_openflights(PLANES_DB):
        if len(p) >= 3:
            icao = clean(p[2]).upper()
            if icao:
                _db["planes"][icao] = {"name": clean(p[0]), "iata": clean(p[1]), "icao": icao}

    # Route index: keyed by airline ICAO/IATA.
    for p in load_openflights(ROUTES_DB):
        if len(p) < 6:
            continue
        airline = clean(p[0]).upper()
        src = clean(p[2]).upper()
        dst = clean(p[4]).upper()
        if airline and src and dst:
            _db["routes"].setdefault(airline, []).append((src, dst))

    _loaded = True
    print("Aviation DB loaded:",
          len(_db["aircraft"]), "aircraft |",
          len(_db["airports"]), "airports |",
          len(_db["airlines"]), "airlines |",
          len(_db["planes"]), "aircraft types")


def nearest_airport(lat, lon):
    best = None
    best_d = float("inf")

    if lat is None or lon is None:
        return None

    for a in _db["airports"]:
        if a["lat"] is None or a["lon"] is None:
            continue
        d = haversine_nm(lat, lon, a["lat"], a["lon"])
        if d < best_d:
            best_d = d
            best = dict(a)
            best["distance_nm"] = round(d, 1)

    return best


def haversine_nm(lat1, lon1, lat2, lon2):
    r = 3440.065
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.atan2(math.sqrt(a), math.sqrt(1-a))


def route_context(airline_code, nearest):
    routes = _db["routes"].get(airline_code.upper(), [])
    if not routes:
        return "--"

    # We intentionally label this as route context, not a live destination.
    if nearest and nearest.get("iata"):
        candidates = []
        for src, dst in routes:
            if src == nearest["iata"] or dst == nearest["iata"]:
                candidates.append(f"{src} → {dst}")
        if candidates:
            return " / ".join(candidates[:2])

    return f"{routes[0][0]} → {routes[0][1]}"


def enrich(plane):
    icao = clean(plane.get("icao")).upper()
    db = _db["aircraft"].get(icao, {})

    typecode = clean(db.get("typecode") or plane.get("typecode")).upper()
    registration = clean(db.get("registration") or plane.get("registration"))
    country = clean(db.get("country") or plane.get("country"))

    type_info = _db["planes"].get(typecode, {})
    aircraft_name = type_info.get("name", "")

    callsign = clean(plane.get("callsign")).upper()
    airline_code = callsign[:3] if len(callsign) >= 3 else ""
    airline_info = _db["airlines"].get(airline_code, {})
    airline_name = airline_info.get("name", "")

    nearest = nearest_airport(
        safe_float(plane.get("latitude")),
        safe_float(plane.get("longitude"))
    )

    return {
        "registration": registration or "--",
        "country": country or "--",
        "typecode": typecode or "--",
        "aircraft_name": aircraft_name or typecode or "--",
        "airline": airline_name or airline_code or "--",
        "nearest_airport": nearest or {},
        "route_context": route_context(airline_code, nearest),
    }


def latlon_to_radar(lat, lon):
    # Local Magdeburg-area radar normalization.
    lat_min, lat_max = 51.2, 53.2
    lon_min, lon_max = 10.0, 13.2

    x = ((lon - lon_min) / (lon_max - lon_min)) * 90 + 5
    y = ((lat_max - lat) / (lat_max - lat_min)) * 80 + 10

    return max(5, min(95, x)), max(5, min(95, y))


def read_aircraft():
    try:
        with open(INPUT_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def map_aircraft(data):
    if data is None:
        return None

    load_databases()
    result = []

    for raw in data.get("aircraft", []):
        lat = raw.get("lat")
        lon = raw.get("lon")
        if lat is None or lon is None:
            continue

        seen = safe_float(raw.get("seen"))
        if seen is not None and seen > MAX_SEEN_SECONDS:
            continue

        icao = clean(raw.get("hex")).upper()
        if not icao:
            continue

        callsign = clean(raw.get("flight")).upper()
        x, y = latlon_to_radar(float(lat), float(lon))

        mapped = {
            "icao": icao,
            "callsign": callsign,
            "latitude": lat,
            "longitude": lon,
            "altitude_ft": raw.get("alt_baro"),
            "geometric_altitude_ft": raw.get("alt_geom"),
            "speed_kt": raw.get("gs"),
            "heading_deg": raw.get("track"),
            "vertical_rate_fpm": raw.get("baro_rate"),
            "distance_nm": raw.get("dst"),
            "direction_deg": raw.get("dir"),
            "seen_sec": seen,
            "position_seen_sec": raw.get("seen_pos"),
            "rssi_db": raw.get("rssi"),
            "x": x,
            "y": y,
        }

        mapped["aviation"] = enrich(mapped)
        result.append(mapped)

    return {
        "timestamp": data.get("now"),
        "receiver": {
            "latitude": RECEIVER_LAT,
            "longitude": RECEIVER_LON
        },
        "aircraft_count": len(result),
        "aircraft": result
    }


def main():
    print("=" * 70)
    print("SKYGUARDIAN — REALTIME AIRCRAFT MAPPER + AVIATION ENRICHMENT")
    print("=" * 70)
    print("Input :", INPUT_FILE)
    print("Output:", OUTPUT_FILE)
    print("DB    :", AVIATION_DIR)

    while True:
        result = map_aircraft(read_aircraft())

        if result is not None:
            tmp = OUTPUT_FILE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(result, f, indent=2)
            tmp.replace(OUTPUT_FILE)

            print(
                f"\rAircraft: {result['aircraft_count']:3d} | "
                f"Updated: {time.strftime('%H:%M:%S')}",
                end="",
                flush=True
            )

        time.sleep(1)


if __name__ == "__main__":
    main()
