# ============================================================
# SKYGUARDIAN TRAJECTORY MAPPER
# ============================================================

import csv
import os
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FEATURE_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "trajectory_features_clean.csv"
)

RISK_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "risk_results.csv"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "trajectory_plots"
)


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 60)
print("SKYGUARDIAN TRAJECTORY MAPPER")
print("=" * 60)
print()

print("Features:")
print(FEATURE_FILE)

print()
print("Risk:")
print(RISK_FILE)

print()
print("Output:")
print(OUTPUT_DIR)

print()


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(FEATURE_FILE):

    print("ERROR: trajectory_features_clean.csv not found.")
    exit(1)


if not os.path.exists(RISK_FILE):

    print("ERROR: risk_results.csv not found.")
    exit(1)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# LOAD TRAJECTORY FEATURES
# ============================================================

print("=" * 60)
print("LOADING TRAJECTORY FEATURES")
print("=" * 60)

aircraft_data = defaultdict(list)

with open(
    FEATURE_FILE,
    "r",
    newline="",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        try:

            icao = row["icao"].strip()

            data = {

                "icao": icao,

                "timestamp":
                    float(row["timestamp"]),

                "latitude":
                    float(row["latitude"]),

                "longitude":
                    float(row["longitude"]),

                "altitude":
                    float(row["altitude"]),

                "speed":
                    float(row["speed"]),

                "heading":
                    float(row["heading"]),

                "vertical_rate":
                    float(row["vertical_rate"]),

                "distance":
                    float(row["distance_from_previous_m"]),

                "time_delta":
                    float(row["time_delta_s"]),

                "altitude_change":
                    float(row["altitude_change_m"]),

                "speed_change":
                    float(row["speed_change_mps"]),

                "heading_change":
                    float(row["heading_change_deg"]),

                "calculated_speed":
                    float(row["calculated_speed_mps"]),

                "acceleration":
                    float(row["acceleration_mps2"])

            }

            aircraft_data[icao].append(data)

        except (ValueError, KeyError):

            continue


print()
print(
    "Aircraft found:",
    len(aircraft_data)
)

for icao, points in aircraft_data.items():

    print(
        f"{icao}: {len(points)} observations"
    )


# ============================================================
# LOAD RISK RESULTS
# ============================================================

print()
print("=" * 60)
print("LOADING RISK RESULTS")
print("=" * 60)

risk_data = {}

with open(
    RISK_FILE,
    "r",
    newline="",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        try:

            icao = row["icao"].strip()

            timestamp = float(
                row["timestamp"]
            )

            key = (
                icao,
                timestamp
            )

            risk_data[key] = {

                "risk":
                    float(
                        row.get(
                            "risk",
                            0
                        )
                    ),

                "status":
                    row.get(
                        "status",
                        "NORMAL"
                    ).strip().upper()

            }

        except (ValueError, KeyError):

            continue


print(
    "Risk records:",
    len(risk_data)
)


# ============================================================
# ADD RISK TO TRAJECTORY POINTS
# ============================================================

for icao, points in aircraft_data.items():

    for point in points:

        key = (
            icao,
            point["timestamp"]
        )

        result = risk_data.get(
            key
        )

        if result:

            point["risk"] = result["risk"]

            point["status"] = result["status"]

        else:

            point["risk"] = 0

            point["status"] = "NORMAL"


# ============================================================
# INDIVIDUAL TRAJECTORY MAPS
# ============================================================

print()
print("=" * 60)
print("CREATING INDIVIDUAL TRAJECTORY MAPS")
print("=" * 60)

for icao, points in aircraft_data.items():

    # --------------------------------------------------------
    # Sort chronologically
    # --------------------------------------------------------

    points.sort(
        key=lambda x: x["timestamp"]
    )

    latitudes = [
        p["latitude"]
        for p in points
    ]

    longitudes = [
        p["longitude"]
        for p in points
    ]

    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    plt.figure(
        figsize=(10, 7)
    )

    plt.plot(
        longitudes,
        latitudes,
        marker=".",
        markersize=3,
        linewidth=1,
        label=icao
    )

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    plt.scatter(
        longitudes[0],
        latitudes[0],
        marker="o",
        s=80,
        label="START"
    )

    # --------------------------------------------------------
    # End
    # --------------------------------------------------------

    plt.scatter(
        longitudes[-1],
        latitudes[-1],
        marker="X",
        s=100,
        label="END"
    )

    # --------------------------------------------------------
    # Mark anomalies
    # --------------------------------------------------------

    anomaly_lats = []
    anomaly_lons = []

    monitor_lats = []
    monitor_lons = []

    for point in points:

        if point["status"] == "ANOMALY":

            anomaly_lats.append(
                point["latitude"]
            )

            anomaly_lons.append(
                point["longitude"]
            )

        elif point["status"] == "MONITOR":

            monitor_lats.append(
                point["latitude"]
            )

            monitor_lons.append(
                point["longitude"]
            )

    if anomaly_lats:

        plt.scatter(
            anomaly_lons,
            anomaly_lats,
            marker="X",
            s=120,
            label="ANOMALY"
        )

    if monitor_lats:

        plt.scatter(
            monitor_lons,
            monitor_lats,
            marker="o",
            s=60,
            label="MONITOR"
        )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    plt.title(
        f"SkyGuardian Trajectory - {icao}"
    )

    plt.xlabel(
        "Longitude"
    )

    plt.ylabel(
        "Latitude"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.legend()

    plt.tight_layout()

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{icao}_trajectory.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"Created: {icao}_trajectory.png"
    )


# ============================================================
# COMBINED MAP
# ============================================================

print()
print("=" * 60)
print("CREATING COMBINED AIRCRAFT MAP")
print("=" * 60)

plt.figure(
    figsize=(12, 9)
)

for icao, points in aircraft_data.items():

    points.sort(
        key=lambda x: x["timestamp"]
    )

    latitudes = [
        p["latitude"]
        for p in points
    ]

    longitudes = [
        p["longitude"]
        for p in points
    ]

    plt.plot(
        longitudes,
        latitudes,
        marker=".",
        markersize=2,
        linewidth=1,
        label=icao
    )


plt.title(
    "SkyGuardian - All Aircraft Trajectories"
)

plt.xlabel(
    "Longitude"
)

plt.ylabel(
    "Latitude"
)

plt.grid(
    True,
    alpha=0.3
)

plt.legend(
    fontsize=8
)

plt.tight_layout()

combined_file = os.path.join(
    OUTPUT_DIR,
    "ALL_AIRCRAFT_TRAJECTORIES.png"
)

plt.savefig(
    combined_file,
    dpi=150
)

plt.close()

print(
    "Created:",
    combined_file
)


# ============================================================
# ALTITUDE VS TIME
# ============================================================

print()
print("=" * 60)
print("CREATING ALTITUDE PLOTS")
print("=" * 60)

for icao, points in aircraft_data.items():

    points.sort(
        key=lambda x: x["timestamp"]
    )

    times = [
        datetime.fromtimestamp(
            p["timestamp"]
        )
        for p in points
    ]

    altitudes = [
        p["altitude"]
        for p in points
    ]

    plt.figure(
        figsize=(10, 5)
    )

    plt.plot(
        times,
        altitudes,
        linewidth=1
    )

    plt.title(
        f"Altitude vs Time - {icao}"
    )

    plt.xlabel(
        "Time"
    )

    plt.ylabel(
        "Altitude (m)"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.xticks(
        rotation=30
    )

    plt.tight_layout()

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{icao}_altitude.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"Created: {icao}_altitude.png"
    )


# ============================================================
# SPEED VS TIME
# ============================================================

print()
print("=" * 60)
print("CREATING SPEED PLOTS")
print("=" * 60)

for icao, points in aircraft_data.items():

    points.sort(
        key=lambda x: x["timestamp"]
    )

    times = [
        datetime.fromtimestamp(
            p["timestamp"]
        )
        for p in points
    ]

    speeds = [
        p["speed"]
        for p in points
    ]

    plt.figure(
        figsize=(10, 5)
    )

    plt.plot(
        times,
        speeds,
        linewidth=1
    )

    plt.title(
        f"Speed vs Time - {icao}"
    )

    plt.xlabel(
        "Time"
    )

    plt.ylabel(
        "Speed (m/s)"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.xticks(
        rotation=30
    )

    plt.tight_layout()

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{icao}_speed.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"Created: {icao}_speed.png"
    )


# ============================================================
# RISK VS TIME
# ============================================================

print()
print("=" * 60)
print("CREATING RISK PLOTS")
print("=" * 60)

for icao, points in aircraft_data.items():

    points.sort(
        key=lambda x: x["timestamp"]
    )

    times = [
        datetime.fromtimestamp(
            p["timestamp"]
        )
        for p in points
    ]

    risks = [
        p["risk"]
        for p in points
    ]

    plt.figure(
        figsize=(10, 5)
    )

    plt.plot(
        times,
        risks,
        linewidth=1
    )

    plt.title(
        f"Risk Score vs Time - {icao}"
    )

    plt.xlabel(
        "Time"
    )

    plt.ylabel(
        "Risk Score"
    )

    plt.ylim(
        0,
        100
    )

    plt.grid(
        True,
        alpha=0.3
    )

    # --------------------------------------------------------
    # Highlight anomaly/monitor points
    # --------------------------------------------------------

    for point in points:

        if point["status"] in (
            "MONITOR",
            "ANOMALY"
        ):

            point_time = datetime.fromtimestamp(
                point["timestamp"]
            )

            plt.scatter(
                point_time,
                point["risk"],
                s=80
            )

    plt.xticks(
        rotation=30
    )

    plt.tight_layout()

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{icao}_risk.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"Created: {icao}_risk.png"
    )


# ============================================================
# PRINT NON-NORMAL EVENTS
# ============================================================

print()
print("=" * 60)
print("NON-NORMAL EVENTS")
print("=" * 60)

event_count = 0

for icao, points in aircraft_data.items():

    for point in points:

        if point["status"] != "NORMAL":

            event_count += 1

            timestamp = datetime.fromtimestamp(
                point["timestamp"]
            )

            print()
            print(
                f"Aircraft : {icao}"
            )

            print(
                f"Time     : {timestamp}"
            )

            print(
                f"Latitude : {point['latitude']}"
            )

            print(
                f"Longitude: {point['longitude']}"
            )

            print(
                f"Altitude : {point['altitude']} m"
            )

            print(
                f"Speed    : {point['speed']} m/s"
            )

            print(
                f"Risk     : {point['risk']}"
            )

            print(
                f"Status   : {point['status']}"
            )


if event_count == 0:

    print()
    print(
        "No MONITOR or ANOMALY events found."
    )


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 60)
print("TRAJECTORY MAPPING COMPLETE")
print("=" * 60)

print()
print(
    "Aircraft mapped:",
    len(aircraft_data)
)

print(
    "Output directory:"
)

print(
    OUTPUT_DIR
)

print()
print("=" * 60)