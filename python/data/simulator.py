import math
import time
import random


class AircraftSimulator:

    def __init__(self):

        self.aircraft = [
            {
                "icao": "ABC123",
                "callsign": "SKY101",
                "lat": 52.1300,
                "lon": 11.6200,
                "altitude": 28000,
                "speed": 440,
                "heading": 275,
                "vertical_rate": 0,
                "status": "NORMAL",
                "risk": 8,
            },

            {
                "icao": "DEF456",
                "callsign": "SKY202",
                "lat": 52.2500,
                "lon": 11.8000,
                "altitude": 32000,
                "speed": 470,
                "heading": 180,
                "vertical_rate": 0,
                "status": "NORMAL",
                "risk": 5,
            },

            {
                "icao": "A1B2C3",
                "callsign": "SKY303",
                "lat": 51.9500,
                "lon": 11.5000,
                "altitude": 12000,
                "speed": 280,
                "heading": 90,
                "vertical_rate": 500,
                "status": "MONITOR",
                "risk": 42,
            },

            {
                "icao": "F4E5D6",
                "callsign": "SKY404",
                "lat": 52.0500,
                "lon": 11.9000,
                "altitude": 22000,
                "speed": 450,
                "heading": 315,
                "vertical_rate": 0,
                "status": "NORMAL",
                "risk": 10,
            },

            {
                "icao": "B7C8D9",
                "callsign": "SKY505",
                "lat": 52.3500,
                "lon": 11.5500,
                "altitude": 35000,
                "speed": 460,
                "heading": 40,
                "vertical_rate": 0,
                "status": "NORMAL",
                "risk": 7,
            },
        ]

        self.last_update = time.time()


    def _move_aircraft(self, plane):

        dt = 2.0

        # Convert knots to km/h
        speed_kmh = plane["speed"] * 1.852

        # Distance travelled in km
        distance_km = speed_kmh * dt / 3600.0

        heading_rad = math.radians(
            plane["heading"]
        )

        # Approximate latitude/longitude movement
        lat_change = (
            distance_km *
            math.cos(heading_rad)
            / 111.0
        )

        lon_scale = max(
            0.2,
            math.cos(
                math.radians(
                    plane["lat"]
                )
            )
        )

        lon_change = (
            distance_km *
            math.sin(heading_rad)
            / (111.0 * lon_scale)
        )

        plane["lat"] += lat_change
        plane["lon"] += lon_change


    def update(self):

        for plane in self.aircraft:

            self._move_aircraft(plane)

            # Small realistic variation
            plane["speed"] += random.uniform(
                -2.0,
                2.0
            )

            plane["speed"] = max(
                100,
                min(
                    550,
                    plane["speed"]
                )
            )

            plane["heading"] += random.uniform(
                -1.5,
                1.5
            )

            plane["heading"] %= 360

            plane["altitude"] += random.randint(
                -50,
                50
            )

            plane["altitude"] = max(
                1000,
                min(
                    45000,
                    plane["altitude"]
                )
            )

            plane["vertical_rate"] = random.randint(
                -100,
                100
            )

            # Risk variation
            if plane["status"] == "NORMAL":
                plane["risk"] = random.randint(
                    5,
                    20
                )

            elif plane["status"] == "MONITOR":
                plane["risk"] = random.randint(
                    30,
                    55
                )

            elif plane["status"] == "ANOMALY":
                plane["risk"] = random.randint(
                    70,
                    95
                )

            plane["timestamp"] = time.time()

        return self.aircraft


    def get_aircraft(self):

        return self.update()


simulator = AircraftSimulator()


def get_aircraft():

    return simulator.get_aircraft()