from arduino.app_utils import App, Bridge
import time


def main():

    print("SKYGUARDIAN BUZZER TEST")

    print("OFF")
    Bridge.call("set_buzzer_mode", 0)
    time.sleep(2)

    print("NEW AIRCRAFT")
    Bridge.call("set_buzzer_mode", 1)
    time.sleep(2)

    print("MONITOR")
    Bridge.call("set_buzzer_mode", 2)
    time.sleep(5)

    print("ANOMALY")
    Bridge.call("set_buzzer_mode", 3)
    time.sleep(5)

    print("OFF")
    Bridge.call("set_buzzer_mode", 0)

    print("TEST COMPLETE")


if __name__ == "__main__":
    App.run(user_loop=main)
