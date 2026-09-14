
# 😀 skyguardian2
# 😀 skyguardian2

SKYGUARDIAN is an offline edge-AI aircraft monitoring system built on the Arduino UNO Q.

## Main Features

- Live 1090 MHz ADS-B reception using RTL-SDR
- Local aircraft decoding using readsb
- Real-time trajectory tracking
- Isolation Forest anomaly detection
- Risk fusion: NORMAL / MONITOR / ANOMALY
- Local WebUI dashboard
- Physical buzzer alerts

## Project Structure

python/
Contains the main Python processing and AI pipeline.

model/
Contains the trained Isolation Forest model and training code.

sketch/
Contains the Arduino UNO Q STM32 firmware for buzzer control.

assets/
Contains the WebUI files.

start_skyguardian.sh
Starts the complete SKYGUARDIAN pipeline.

stop_skyguardian.sh
Stops the running SKYGUARDIAN processes.

*.yaml / *.yml
Configuration files required by the application or App Lab environment.

## Running

After connecting the RTL-SDR and ADS-B antenna, run:

./start_skyguardian.sh

The script starts the complete processing pipeline and local dashboard.

To stop the system:

./stop_skyguardian.sh

## Data

OpenSky aviation datasets are used for model development and flight analysis.
Live aircraft data is received locally through the RTL-SDR and decoded using readsb.

All real-time processing and ML inference are performed locally on the Arduino UNO Q.








