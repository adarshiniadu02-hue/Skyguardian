import csv


class OpenSkyLoader:

    def __init__(self, csv_file):
        self.csv_file = csv_file

    def stream(self):

        with open(self.csv_file, "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:
                    lat = float(row["lat"])
                    lon = float(row["lon"])

                    if not (-90 <= lat <= 90):
                        continue

                    if not (-180 <= lon <= 180):
                        continue

                    yield {
                        "icao": row["icao24"].strip().upper(),

                        "timestamp": float(row["time"]),

                        "latitude": lat,
                        "longitude": lon,

                        "speed": float(row["velocity"])
                        if row["velocity"] else None,

                        "heading": float(row["heading"])
                        if row["heading"] else None,

                        "vertical_rate": float(row["vertrate"])
                        if row["vertrate"] else None,

                        "altitude": float(row["baroaltitude"])
                        if row["baroaltitude"] else None,

                        "geoaltitude": float(row["geoaltitude"])
                        if row["geoaltitude"] else None,

                        "callsign": row["callsign"].strip()
                        if row["callsign"]
                        else "",

                        "onground": row["onground"].lower() == "true",

                        "squawk": row["squawk"].strip()
                        if row["squawk"]
                        else None
                    }

                except (ValueError, TypeError, KeyError):
                    continue
