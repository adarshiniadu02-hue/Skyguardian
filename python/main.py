from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI
import time


# ==================================================
# WEB UI
# ==================================================

ui = WebUI()


# ==================================================
# AIRCRAFT DATA
# ==================================================

aircraft = {

    "ABC123": {
        "altitude": "28,000 ft",
        "speed": "440 kt",
        "heading": "275°",
        "status": "NORMAL"
    },

    "DEF456": {
        "altitude": "32,000 ft",
        "speed": "470 kt",
        "heading": "180°",
        "status": "NORMAL"
    },

    "A1B2C3": {
        "altitude": "12,000 ft",
        "speed": "280 kt",
        "heading": "090°",
        "status": "MONITOR"
    },

    "F4E5D6": {
        "altitude": "22,000 ft",
        "speed": "510 kt",
        "heading": "315°",
        "status": "ANOMALY"
    },

    "B7C8D9": {
        "altitude": "35,000 ft",
        "speed": "460 kt",
        "heading": "040°",
        "status": "NORMAL"
    }
}


# ==================================================
# LED CONTROL
# ==================================================

def set_led_for_status(status):

    status = status.upper()

    print("================================")
    print("Setting LED for:", status)

    try:

        if status == "NORMAL":

            # GREEN
            Bridge.call(
                "set_led3_color",
                0,
                255,
                0
            )

            print("LED COMMAND SENT: GREEN")

        else:

            # RED
            Bridge.call(
                "set_led3_color",
                255,
                0,
                0
            )

            print("LED COMMAND SENT: RED")

    except Exception as e:

        print("LED ERROR:")
        print(e)


# ==================================================
# AIRCRAFT SELECTED
# ==================================================

def on_aircraft_selected(id, message):

    print("================================")
    print("AIRCRAFT SELECTION RECEIVED")
    print("ID:", id)
    print("MESSAGE:", message)

    try:

        icao = message.get("icao")

        if not icao:

            print("ERROR: No ICAO received")

            return


        if icao not in aircraft:

            print("ERROR: Unknown aircraft:", icao)

            return


        selected = aircraft[icao]

        status = selected["status"]


        print("Selected aircraft:", icao)

        print("Status:", status)


        # ==========================================
        # CONTROL UNO Q LED
        # ==========================================

        set_led_for_status(status)


        # ==========================================
        # SEND CONFIRMATION TO WEB UI
        # ==========================================

        ui.send_message(
            "aircraft_selected",
            {
                "icao": icao,
                "altitude": selected["altitude"],
                "speed": selected["speed"],
                "heading": selected["heading"],
                "status": status
            }
        )


    except Exception as e:

        print("AIRCRAFT SELECTION ERROR:")

        print(e)


# ==================================================
# WEB UI CONNECTION
# ==================================================

def on_connect(connection):

    print("WEB UI CONNECTED")


def on_disconnect(connection):

    print("WEB UI DISCONNECTED")


ui.on_connect(on_connect)

ui.on_disconnect(on_disconnect)


# ==================================================
# WEB UI MESSAGE
# ==================================================

ui.on_message(
    "select_aircraft",
    on_aircraft_selected
)


# ==================================================
# MAIN LOOP
# ==================================================

def loop():

    time.sleep(1)


# ==================================================
# START
# ==================================================

print("================================")
print("SKYGUARDIAN STARTED")
print("================================")

App.run(
    user_loop=loop
)