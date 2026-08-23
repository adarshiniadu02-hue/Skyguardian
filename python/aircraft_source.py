import random


aircraft = [

    {
        "icao": "ABC123",
        "altitude": 28000,
        "speed": 440,
        "heading": 275,
        "x": 20,
        "y": 20,
        "status": "NORMAL",
        "risk": 12
    },

    {
        "icao": "DEF456",
        "altitude": 32000,
        "speed": 470,
        "heading": 180,
        "x": 60,
        "y": 35,
        "status": "NORMAL",
        "risk": 8
    },

    {
        "icao": "A1B2C3",
        "altitude": 12000,
        "speed": 280,
        "heading": 90,
        "x": 30,
        "y": 65,
        "status": "MONITOR",
        "risk": 42
    },

    {
        "icao": "F4E5D6",
        "altitude": 22000,
        "speed": 510,
        "heading": 315,
        "x": 80,
        "y": 55,
        "status": "ANOMALY",
        "risk": 82
    },

    {
        "icao": "B7C8D9",
        "altitude": 35000,
        "speed": 460,
        "heading": 40,
        "x": 60,
        "y": 75,
        "status": "NORMAL",
        "risk": 15
    }

]


def get_aircraft():

    for plane in aircraft:

        # Simulate aircraft movement

        plane["x"] += random.uniform(-1.5, 1.5)
        plane["y"] += random.uniform(-1.0, 1.0)

        # Keep aircraft inside map

        plane["x"] = max(
            5,
            min(95, plane["x"])
        )

        plane["y"] = max(
            5,
            min(90, plane["y"])
        )

        # Simulate flight changes

        plane["altitude"] += random.randint(
            -100,
            100
        )

        plane["speed"] += random.randint(
            -3,
            3
        )

        plane["heading"] += random.randint(
            -2,
            2
        )

        # Keep heading 0-359

        plane["heading"] %= 360

    return aircraft