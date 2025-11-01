# IoT Smart Mobile Robot (Raspberry Pi)

Telemetry (IR line sensors, ultrasonic distance, camera status) → **Adafruit IO** via MQTT.

> Code lives under `src/`, configs in `config/`, logs/data excluded from git.

---

## Table of Contents

* [Team](#team)
* [System Overview](#system-overview)
* [Repository Layout](#repository-layout)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Configuration](#configuration)

  * [Adafruit IO](#adafruit-io)
  * [App Settings (optional)](#app-settings-optional)
* [How to Run](#how-to-run)

  * [A) Manual Driving UI](#a-manual-driving-ui)
  * [B) Line Follower (Autonomous)](#b-line-follower-autonomous)
  * [C) Telemetry Publisher](#c-telemetry-publisher)
  * [Typical Two-Terminal Setup](#typical-two-terminal-setup)
* [Adafruit IO Dashboard](#adafruit-io-dashboard)
* [Data Logging](#data-logging)

  * [Daily Rotation & Upload (optional)](#daily-rotation--upload-optional)
* [Auto-Start (optional)](#auto-start-optional)
* [Data Format Spec](#data-format-spec)
* [Safety Notes](#safety-notes)
* [Known Limitations / Future Work](#known-limitations--future-work)
* [Grading Checklist](#grading-checklist)
* [License](#license)
* [Quick Commands](#quick-commands)

---

## Team

* **Amine Baha** (`@AmineBaha-oss`) — hardware + software
* **Tamim Afghanyar** — software + testing

---

## System Overview

* **Sensing layer:** IR triplet (line-follow), Ultrasonic (obstacles), Camera (status + optional thumbnail).
* **Control layer:** Manual driving via `car_tui.py`; autonomous line-follow via `line_follow.py` (PID + pivot).
* **Comms layer:** MQTT to Adafruit IO (feeds for sensors + status).
* **Data layer:** CSV logs with ISO timestamps, 1 file/day.

```
[IR/Ultrasonic/Camera] --> car_tui & line_follow --> /tmp caches
                                      \--> telemetry.py --> Adafruit IO + CSV
```

---

## Repository Layout

```
repo/
├─ src/
│  ├─ car_tui.py               # Terminal UI (driving + starts/stops line follow)
│  ├─ line_follow.py           # PID line follower (writes IR cache)
│  ├─ telemetry.py             # Publishes caches → Adafruit IO, logs CSV
│  ├─ ir_cache_writer.py      
│  ├─ ir_cache_publisher.py    
│  ├─ ultra_cache_writer.py   
│  ├─ ultrasonic.py, infrared.py 
│  ├─ run_telemetry.sh        
│  └─ ... (LED, motor, server files)
├─ config/
│  ├─ adafruit.sample.json     
│  └─ app.sample.json        
├─ logs/                     
├─ data/                      
├─ systemd/                   
├─ cron/                       
├─ docs/                       # figures/screenshots for report
├─ requirements.txt
└─ README.md
```


---

## Prerequisites

* Raspberry Pi OS (64-bit) on **Pi 4B**
* **Python 3.9+**
* Enable **SPI**, **I2C**, **Camera** as needed via `raspi-config`
* OpenCV for Python (installed below)

---

## Installation

```bash
sudo apt update
sudo apt install -y python3-venv python3-opencv

# clone your repo (example)
# git clone https://github.com/<you>/<repo>.git
cd repo

# set up venv
python3 -m venv .venv
source .venv/bin/activate

# python deps
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





## How to Run

### A) Manual Driving UI (also writes caches for telemetry)

```bash
cd repo/src
python3 car_tui.py
```

**Keys:** `WASD` drive, `SPACE` stop, `L/K` start/stop line-follow, `U` toggle ultrasonic readout, arrow keys pan/tilt, `T` LEDs, `Q` quit.

### B) Line Follower (Autonomous)

```bash
cd repo/src
python3 line_follow.py
```

Writes IR states to `/tmp/ir_triplet.txt` and `/tmp/line_state.txt`.

### C) Telemetry Publisher (reads caches → Adafruit IO + CSV)

```bash
cd repo/src
./run_telemetry.sh
# or
python3 telemetry.py
```

### Typical Two-Terminal Setup

* **Terminal 1:** `python3 car_tui.py` (GPIO in use here)
* **Terminal 2:** `python3 telemetry.py` (cache only → no GPIO conflict)

---

## Adafruit IO Dashboard

Create a dashboard and add widgets for these feeds:

* `line-ir-left`, `line-ir-center`, `line-ir-right` (0/1)
* `line-state` (e.g., `L`, `M`, `R`, `LM`, `LR`, `LMR`, `NONE`)
* `ultra-distance` (cm)
* `cam-status` (online/offline); optional `cam-thumb` (base64 jpg)

---

## Data Logging

CSV written to `logs/telemetry_YYYY-MM-DD.csv` with header:

```
time,ultrasonic_cm,ir_left,ir_center,ir_right,line_state,camera_status
```

Timestamps are local **ISO 8601**.

**Example row:**

```text
2025-11-01T02:05:12,23.7,1,0,0,L__,online
```




## Data Format Spec

* **ultrasonic_cm:** float (cm), valid `0 < d ≤ 400`
* **ir_left/center/right:** integers `0|1`
* **line_state:** `L`, `M`, `R`, combos (`LM`, `LR`, `LMR`) or `NONE`
* **camera_status:** `online|offline|idle`

---

## Safety Notes

* Low-voltage only; fuse or polyfuse on battery lines.
* Separate power for motors/servos; **common ground** with Pi.
* Start at low speeds; keep an **emergency stop** available.

---


## Quick Commands

```bash
# venv
cd repo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# configs
cp config/adafruit.sample.json config/adafruit.json
cp config/app.sample.json      config/app.json

# run UI + telemetry
cd src
python3 car_tui.py
python3 telemetry.py
```
