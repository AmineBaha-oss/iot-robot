# YVLSWITCH

IoT Smart Mobile Robot (Raspberry Pi) — Complete IoT system with telemetry, autonomous navigation, and **Flask web application** for remote monitoring and control.

> Organized codebase with modular structure: hardware interfaces, server modules, telemetry utilities, Flask web app, and database sync.

![Iot-Robot-Image](https://github.com/user-attachments/assets/b92f23f6-80a3-4ba6-83ea-996ce9e3bfbb)

## Milestone 3 - Submission Information

### Team Members

- **Amine Baha** (Student ID: 2332522) — hardware + software
- **Tamim Afghanyar** — software + testing

### Adafruit IO Dashboard

**Dashboard Link:** [Add your Adafruit IO dashboard link here]

- Live sensor data visualization
- Real-time graphs for ultrasonic, IR sensors, line state
- Control feeds for motor, LED, buzzer, line tracking, obstacle avoidance

### Cloud Database (Neon.com)

**Database Link:** [Add your Neon.com project link here]

- PostgreSQL database for historical sensor data
- Automatic sync from Raspberry Pi local SQLite
- Queryable via Flask web application

### Video Demonstration

**YouTube Link:** https://www.youtube.com/watch?v=mzLmGYfJ0nY

### Project Reflection

This project represents a comprehensive IoT mobile robot system with autonomous navigation capabilities. One of the most challenging aspects was **configuring the line-following algorithm to be consistent and reliable**. Achieving stable line tracking required extensive tuning of PID parameters, careful calibration of infrared sensors, and implementing pivot modes for handling sharp turns. Balancing responsiveness with stability proved to be a delicate process that required numerous iterations and real-world testing to achieve the desired performance.

**What worked well:** The modular architecture of the codebase allows for easy maintenance and future enhancements, with clear separation between hardware interfaces, control logic, and telemetry systems. The Flask web application provides a user-friendly interface for remote monitoring and control, and the database sync mechanism ensures data integrity even during internet outages.

**What was hardest:** Integrating the offline data storage with cloud synchronization was challenging, requiring careful handling of connection states and ensuring no data loss during transitions. Additionally, coordinating commands between the Flask app, Adafruit IO, and the Raspberry Pi required precise timing and error handling.

**What we'd improve:** If we had more time, we would implement a more sophisticated dashboard with real-time video streaming, add more sensor types, implement machine learning for improved obstacle avoidance, and add user authentication to the web application for better security.

---

## Table of Contents

- [Team](#team)
- [System Overview](#system-overview)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Adafruit IO](#adafruit-io)
  - [App Settings (optional)](#app-settings-optional)
- [How to Run](#how-to-run)
  - [A) Manual Driving UI](#a-manual-driving-ui)
  - [B) Line Follower (Autonomous)](#b-line-follower-autonomous)
  - [C) Obstacle Navigator](#c-obstacle-navigator)
  - [D) Telemetry Publisher](#d-telemetry-publisher)
  - [E) Server Application (PyQt)](#e-server-application-pyqt)
  - [F) Flask Web Application](#f-flask-web-application)
  - [G) Command Listener (Raspberry Pi)](#g-command-listener-raspberry-pi)
  - [Typical Two-Terminal Setup](#typical-two-terminal-setup)
- [Adafruit IO Dashboard](#adafruit-io-dashboard)
- [Data Logging](#data-logging)
- [Auto-Start (optional)](#auto-start-optional)
- [Data Format Spec](#data-format-spec)
- [Safety Notes](#safety-notes)
- [Quick Commands](#quick-commands)

---

## Team

- **Amine Baha** (`@AmineBaha-oss`) — hardware + software
- **Tamim Afghanyar** — software + testing

---

## System Overview

- **Sensing layer:** IR triplet (line-follow), Ultrasonic (obstacles), Camera (status + optional thumbnail).
- **Control layer:** Manual driving via `car_tui.py`; autonomous line-follow via `line_follow.py` (PID + pivot); obstacle avoidance via `obstacle_navigator.py`.
- **Comms layer:** MQTT to Adafruit IO (feeds for sensors + status); TCP server for remote control; **Flask web app** for HTTP-based control.
- **Data layer:** CSV logs with ISO timestamps, 1 file/day; **SQLite local database** with automatic sync to **Neon.com PostgreSQL**.
- **Web layer:** Flask application with 6 pages (Home, About, Sensor Data, Control Car, Line Tracking, Obstacle Avoidance) deployed on **Render.com**.

```
[IR/Ultrasonic/Camera] --> car_tui & line_follow --> /tmp caches
                                      \--> telemetry/ --> Adafruit IO
                                                         \--> Flask Web App (Render.com)
                                                         \--> Local SQLite --> Neon.com PostgreSQL
```

---

## Repository Layout

```
YVLSWITCH/
├── app.py                     # Flask web application (deploy to Render.com)
├── config/                    # Configuration files
│   ├── adafruit.sample.json   # Adafruit IO credentials template
│   ├── adafruit.json          # Adafruit IO credentials (not in git)
│   ├── app.sample.json        # App settings template
│   └── params.json            # Hardware parameters (auto-generated)
├── templates/                 # Flask HTML templates
│   ├── base.html              # Base template with navigation
│   ├── home.html              # Dashboard/home page
│   ├── about.html             # About page
│   ├── sensor_data.html       # Historical sensor data with charts
│   ├── control_car.html       # Remote car control
│   ├── line_tracking.html     # Line tracking control
│   └── obstacle_avoidance.html # Obstacle avoidance control
├── static/                    # Static web assets
│   ├── css/
│   │   └── style.css          # Modern dark theme styling
│   └── js/
│       └── main.js            # JavaScript utilities
├── db/                        # Local SQLite database (git-ignored)
│   └── robot_telemetry.db     # Local offline storage
├── data/                      # CSV log files (git-ignored)
│   └── YYYY-MM-DD_robot_telemetry.csv
├── docs/                      # Documentation files
├── scripts/                   # Shell scripts
│   ├── run_telemetry.sh       # Start telemetry daemon
│   └── tail_today.sh          # Tail today's CSV log
├── src/                       # Source code
│   ├── hardware/             # Hardware interfaces
│   │   ├── adc.py            # Analog-to-digital converter
│   │   ├── buzzer.py          # Buzzer control
│   │   ├── camera.py          # Camera interface
│   │   ├── infrared.py        # IR line sensors
│   │   ├── led.py             # LED strip control
│   │   ├── motor.py           # Motor control (PCA9685)
│   │   ├── pca9685.py         # PWM controller
│   │   ├── photoresistor.py  # Light sensors
│   │   ├── rpi_ledpixel.py    # WS281X LED driver
│   │   ├── servo.py           # Servo motor control
│   │   ├── spi_ledpixel.py    # SPI LED driver
│   │   └── ultrasonic.py      # Distance sensor
│   ├── telemetry/             # Telemetry & publishing
│   │   ├── ir_cache_publisher.py
│   │   ├── ir_cache_writer.py
│   │   ├── ir_stdout_to_cache.py
│   │   ├── telemetry.py        # Main telemetry module
│   │   ├── telemetry_daemon.py # Telemetry daemon
│   │   ├── telemetry_runner.py # Telemetry runner script
│   │   └── ultra_cache_writer.py
│   ├── database_sync.py       # Database sync module (SQLite ↔ Neon.com)
│   ├── command_listener.py    # MQTT command listener for web app
│   ├── car.py                 # Main car control class
│   ├── car_tui.py             # Terminal UI (curses)
│   ├── line_follow.py         # Line following algorithm (PID)
│   ├── main.py                # Server application (PyQt)
│   ├── obstacle_navigator.py  # Obstacle avoidance
│   └── parameter.py           # Parameter manager
├── DEPLOYMENT_GUIDE.md        # Deployment instructions (Neon.com + Render.com)
├── FLASK_SETUP.md             # Flask app setup guide
├── MILESTONE3_SUMMARY.md      # Milestone 3 summary
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Raspberry Pi OS (64-bit) on **Pi 4B or Pi 5**
- **Python 3.9+**
- Enable **SPI**, **I2C**, **Camera** as needed via `raspi-config`
- OpenCV for Python (optional, for camera support)

---

## Installation

```bash
# System dependencies
sudo apt update
sudo apt install -y python3-venv python3-opencv python3-smbus

# Clone repository
git clone https://github.com/<your-username>/YVLSWITCH.git
cd YVLSWITCH

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## Configuration

### Adafruit IO

Copy the sample and fill in your username/key & feed names:

```bash
cp config/adafruit.sample.json config/adafruit.json
nano config/adafruit.json
```

Example:

```json
{
  "adafruit": {
    "username": "YOUR_USER",
    "key": "aio_xxx",
    "feeds": {
      "ultrasonic_cm": "ultra-distance",
      "ir_left": "line-ir-left",
      "ir_center": "line-ir-center",
      "ir_right": "line-ir-right",
      "line_state": "line-state",
      "camera_status": "cam-status",
      "camera_thumb": "cam-thumb"
    }
  }
}
```

### App Settings (optional)

```bash
cp config/app.sample.json config/app.local.json
nano config/app.local.json
```

Configure intervals and timezone:

```json
{
  "timezone": "America/Toronto",
  "intervals": {
    "ultrasonic_sec": 0.5,
    "infrared_sec": 0.2,
    "camera_sec": 5.0
  },
  "local_log": {
    "enabled": true,
    "path": "data/2025-11-01_robot_telemetry.csv"
  }
}
```

### Hardware Parameters

The `parameter.py` module will automatically prompt for hardware versions on first run, or you can manually configure `config/params.json`:

```json
{
  "Connect_Version": 2,
  "Pcb_Version": 1,
  "Pi_Version": 2
}
```

---

## How to Run

### A) Manual Driving UI

Terminal-based control interface with real-time sensor display:

```bash
cd src
python3 car_tui.py
```

**Controls:**

- `W` - Forward | `S` - Backward | `A` - Turn Left | `D` - Turn Right
- `SPACE` - Stop
- `L` - Start Line Follow | `K` - Stop Line Follow
- `O` - Start Obstacle Navigator | `P` - Stop Obstacle Navigator
- `U` - Toggle ultrasonic readout
- `↑/↓` - Tilt head | `←/→` - Pan head | `H` - Home head
- `[`/`]` - Decrease/Increase speed
- `{`/`}` - Decrease/Increase turn power
- `B` - Buzzer | `T` - Toggle LEDs
- `Q` - Quit

### B) Line Follower (Autonomous)

PID-based line following with pivot mode for sharp turns:

```bash
cd src
python3 line_follow.py [options]
```

**Common options:**

```bash
# Basic usage
python3 line_follow.py

# Custom sensor order and inversion
python3 line_follow.py --sensor-order "1,2,3" --active-low

# Adjust PID gains
python3 line_follow.py --kp 1000 --kd 380

# Enable pivot mode for sharp turns
python3 line_follow.py --pivot --pivot-err 0.6 --pivot-power 1200
```

Writes IR states to `/tmp/ir_lmr.txt` and `/tmp/line_state.txt` for telemetry.

### C) Obstacle Navigator

Ultrasonic-based obstacle avoidance with pan/tilt servo scanning:

```bash
cd src
python3 obstacle_navigator.py [options]
```

**Common options:**

```bash
# Basic usage
python3 obstacle_navigator.py

# Adjust obstacle threshold
python3 obstacle_navigator.py --obs-th 45.0

# Custom servo ranges
python3 obstacle_navigator.py --pan-min 10 --pan-max 170 --tilt-min 60 --tilt-max 120
```

### D) Telemetry Publisher

Reads sensor caches and publishes to Adafruit IO + logs CSV:

```bash
# Option 1: Using script
./scripts/run_telemetry.sh

# Option 2: Direct Python
cd src/telemetry
python3 telemetry_daemon.py
```

### E) Server Application (PyQt)

GUI server application for remote control:

```bash
cd src
python3 main.py

# Headless mode (no GUI)
python3 main.py --terminal
```

### F) Flask Web Application

Modern web interface for remote monitoring and control, deployed on Render.com:

**Features:**

- **6 Pages:** Home Dashboard, About, Sensor Data, Control Car, Line Tracking, Obstacle Avoidance
- **Live Data:** Real-time sensor readings from Adafruit IO via HTTP
- **Historical Data:** Chart.js graphs with date selection from cloud database
- **Remote Control:** Control motors (forward/backward/left/right), LEDs, buzzer
- **Algorithm Control:** Start/stop line tracking and obstacle avoidance
- **Database Sync:** Local SQLite for offline storage, automatic sync to Neon.com PostgreSQL

**Local Development:**

```bash
# Install Flask dependencies
pip install -r requirements.txt

# Run locally
python app.py
# App available at http://localhost:5000
```

**Deployment to Render.com:**

1. Push code to GitHub
2. Create Web Service on Render.com
3. Set environment variables:
   - `DATABASE_URL` (from Neon.com)
   - `SECRET_KEY` (generate random key)
4. Deploy!

See `DEPLOYMENT_GUIDE.md` and `FLASK_SETUP.md` for detailed instructions.

### G) Command Listener (Raspberry Pi)

Listens to Adafruit IO MQTT feeds for web app commands:

```bash
cd src
python3 command_listener.py
```

This script subscribes to control feeds and executes commands:

- Motor control (forward, backward, left, right, stop)
- LED control (on, off)
- Buzzer control (on, off)
- Line tracking (start, stop)
- Obstacle avoidance (start, stop)

**Note:** Run this on the Raspberry Pi to receive commands from the Flask web app.

### Typical Two-Terminal Setup

- **Terminal 1:** `python3 car_tui.py` (GPIO in use here)
- **Terminal 2:** `./scripts/run_telemetry.sh` (cache only → no GPIO conflict)
- **Terminal 3 (optional):** `python3 src/command_listener.py` (for web app control)

---

## Adafruit IO Dashboard

Create a dashboard and add widgets for these feeds:

**Sensor Feeds (for monitoring):**

- `line-ir-left`, `line-ir-center`, `line-ir-right` (0/1)
- `line-state` (e.g., `L`, `M`, `R`, `LM`, `LR`, `LMR`, `___`)
- `ultra-distance` (cm)
- `cam-status` (online/offline); optional `cam-thumb` (base64 jpg)

**Control Feeds (for web app commands):**

- `motor-control` (forward, backward, left, right, stop)
- `led-control` (on, off)
- `buzzer-control` (on, off)
- `line-tracking` (start, stop)
- `obstacle-avoidance` (start, stop)

---

## Data Logging

**CSV Files:**
CSV written to `data/YYYY-MM-DD_robot_telemetry.csv` with header:

```
timestamp_iso,ultrasonic_cm,ir_left,ir_center,ir_right,line_state
```

Timestamps are local **ISO 8601** format.

**Example row:**

```text
2025-11-01T02:05:12,23.7,1,0,0,L__
```

**Database Storage:**

- **Local SQLite:** `db/robot_telemetry.db` - Stores data when offline
- **Cloud PostgreSQL:** Neon.com - Historical data storage
- **Auto-sync:** Background worker syncs local DB to cloud every 5 minutes
- **Offline Support:** Data stored locally when internet is down, synced when connection restored

---

## Data Format Spec

- **ultrasonic_cm:** float (cm), valid `0 < d ≤ 400`
- **ir_left/center/right:** integers `0|1`
- **line_state:** `L`, `M`, `R`, combos (`LM`, `LR`, `LMR`) or `___`
- **camera_status:** `online|offline|idle`

---

## Safety Notes

- Low-voltage only; fuse or polyfuse on battery lines.
- Separate power for motors/servos; **common ground** with Pi.
- Start at low speeds; keep an **emergency stop** available.
- Test in a safe, open area before autonomous operation.

---

## Quick Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configuration
cp config/adafruit.sample.json config/adafruit.json
cp config/app.sample.json config/app.local.json
nano config/adafruit.json  # Add your credentials

# Run applications (Raspberry Pi)
cd src
python3 car_tui.py              # Manual control UI
python3 line_follow.py          # Line following
python3 obstacle_navigator.py   # Obstacle avoidance
python3 main.py                 # Server GUI
python3 command_listener.py     # Web app command listener

# Telemetry (separate terminal)
./scripts/run_telemetry.sh

# View logs
./scripts/tail_today.sh

# Flask Web App (local development)
python app.py                   # Run Flask app locally
# Or deploy to Render.com (see DEPLOYMENT_GUIDE.md)
```

---

---

## Web Application Features

The Flask web application provides:

- **Real-time Monitoring:** Live sensor data updates every 2 seconds
- **Historical Analysis:** Chart.js graphs for any date with data selection
- **Remote Control:** Full motor control (forward, backward, left, right, stop)
- **Device Management:** Control LEDs and buzzer remotely
- **Algorithm Control:** Start/stop line tracking and obstacle avoidance from web interface
- **Offline Support:** Local SQLite database stores data when offline, syncs automatically
- **Modern UI:** Dark theme with responsive design, similar to DomiSafe example

**Access:** Deploy to Render.com and access from any device with a web browser.

## Deployment

- **Flask App:** Deploy to Render.com (see `DEPLOYMENT_GUIDE.md`)
- **Database:** Neon.com PostgreSQL (free tier available)
- **Adafruit IO:** Cloud MQTT platform for sensor data
- **Raspberry Pi:** Runs telemetry daemon and command listener

See `DEPLOYMENT_GUIDE.md` for step-by-step deployment instructions.

---

**Note:** This project is organized with a modular structure for maintainability. Hardware interfaces are separated from control logic, telemetry utilities are isolated to prevent conflicts, and the Flask web application provides a modern interface for remote monitoring and control.
