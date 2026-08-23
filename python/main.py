from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI
import time

ui = WebUI()

connected = False
selected_icao = "ABC123"

# Simulated aircraft
aircraft = [
    {
        "icao": "ABC123",
        "altitude": 28000,
        "speed": 440,
        "heading": 275,
        "x": 25,
        "y": 25,
        "status": "NORMAL",
        "risk": 12
    },
    {
        "icao": "DEF456",
        "altitude": 32000,
        "speed": 470,
        "heading": 180,
        "x": 70,
        "y": 25,
        "status": "NORMAL",
        "risk": 8
    },
    {
        "icao": "A1B2C3",
        "altitude": 12000,
        "speed": 280,
        "heading": 90,
        "x": 30,
        "y": 70,
        "status": "MONITOR",
        "risk": 42
    },
    {
        "icao": "F4E5D6",
        "altitude": 22000,
        "speed": 510,
        "heading": 315,
        "x": 72,
        "y": 65,
        "status": "ANOMALY",
        "risk": 82
    },
    {
        "icao": "B7C8D9",
        "altitude": 35000,
        "speed": 460,
        "heading": 40,
        "x": 50,
        "y": 45,
        "status": "NORMAL",
        "risk": 15
    }
]


# ==========================================
# WEB UI CONNECTION
# ==========================================

def on_connect(client_id):

    global connected

    connected = True

    print("Web UI connected")


def on_disconnect(client_id):

    global connected

    connected = False

    print("Web UI disconnected")


# ==========================================
# AIRCRAFT SELECTION
# ==========================================

def on_aircraft_selected(client_id, data):

    global selected_icao

    try:

        selected_icao = data["icao"]

        print(
            f"✈ Selected aircraft: {selected_icao}"
        )

        # Find selected aircraft
        selected = None

        for plane in aircraft:

            if plane["icao"] == selected_icao:

                selected = plane
                break

        if selected:

            # LED 3:
            # GREEN = NORMAL
            # RED = anything else

            if selected["status"] == "NORMAL":

                try:

                    Bridge.call(
                        "set_led3_color",
                        0,
                        255,
                        0
                    )

                    print("🟢 LED GREEN")

                except Exception as e:

                    print(
                        f"LED error: {e}"
                    )

            else:

                try:

                    Bridge.call(
                        "set_led3_color",
                        255,
                        0,
                        0
                    )

                    print("🔴 LED RED")

                except Exception as e:

                    print(
                        f"LED error: {e}"
                    )

    except Exception as e:

        print(
            f"Aircraft selection error: {e}"
        )


# ==========================================
# MOVE AIRCRAFT
# ==========================================

def move_aircraft():

    # Simple deterministic movement

    aircraft[0]["x"] += 0.25
    aircraft[1]["x"] -= 0.20
    aircraft[2]["y"] -= 0.18
    aircraft[3]["x"] -= 0.15
    aircraft[4]["y"] += 0.15

    # Keep aircraft inside radar

    for plane in aircraft:

        if plane["x"] > 88:
            plane["x"] = 12

        if plane["x"] < 12:
            plane["x"] = 88

        if plane["y"] > 88:
            plane["y"] = 12

        if plane["y"] < 12:
            plane["y"] = 88


# ==========================================
# SEND DATA TO WEB UI
# ==========================================

def send_aircraft_data():

    anomaly_count = sum(
        1
        for plane in aircraft
        if plane["status"] == "ANOMALY"
    )

    selected = None

    for plane in aircraft:

        if plane["icao"] == selected_icao:

            selected = plane
            break

    risk = 0

    if selected:

        risk = selected["risk"]

    ui.send_message(
        "aircraft_data",
        {
            "aircraft": aircraft,
            "aircraft_count": len(aircraft),
            "anomaly_count": anomaly_count,
            "selected_icao": selected_icao,
            "risk": risk
        }
    )


# ==========================================
# MAIN LOOP
# ==========================================

def loop():

    if connected:

        move_aircraft()

        send_aircraft_data()

    time.sleep(1)


# ==========================================
# REGISTER CALLBACKS
# ==========================================

ui.on_connect(on_connect)

ui.on_disconnect(on_disconnect)

ui.on_message(
    "aircraft_selected",
    on_aircraft_selected
)


# ==========================================
# START APP
# ==========================================

print("SkyGuardian started")

App.run(user_loop=loop)