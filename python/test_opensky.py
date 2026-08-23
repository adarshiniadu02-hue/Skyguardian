from data.opensky_loader import OpenSkyLoader


CSV_FILE = "/home/arduino/ArduinoApps/SkyGuardian-ML/data/raw/states_2018-05-28-00.csv"


loader = OpenSkyLoader(CSV_FILE)

count = 0

for aircraft in loader.stream():

    print(aircraft)

    count += 1

    if count >= 10:
        break

print()
print("Successfully read", count, "aircraft observations.")
