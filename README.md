# IoT Optical Dust Monitoring System

An end-to-end, edge-to-cloud environmental monitoring platform
engineered to detect, calibrate, persist, and visualize airborne dust
density in real time \[cite: 5\].

The architecture utilizes an **ESP32** microcontroller interfaced with a
**Sharp GP2Y1014AU0F optical dust sensor**, transmitting telemetry over
Wi-Fi via HTTP POST to a containerized **FastAPI** backend \[cite: 4,
5\]. Data is persisted in an **SQLite** database and streamed to a
dynamic, auto-polling **Chart.js** web dashboard \[cite: 5, 8, 9\].

------------------------------------------------------------------------

## System Architecture

``` text
┌─────────────────────────────────┐
│     Sharp GP2Y1014AU0F           │
│     Optical Dust Sensor          │
└────────────────┬────────────────┘
                 │ Analog Vo (0–3.3 V ADC)
                 ▼
┌─────────────────────────────────┐
│     ESP32 Microcontroller        │
│     (Signal Conditioning)        │
│  • 280 µs IRED trigger pulse     │
│  • Linear voltage-to-density     │
│    conversion (µg/m³)            │
└────────────────┬────────────────┘
                 │ JSON telemetry over Wi-Fi (HTTP POST)
                 ▼
┌─────────────────────────────────┐
│     Containerized FastAPI        │
│     (Docker / Cloud / Local)     │
│  • Ingestion REST API (port 8000)│
│  • Serves static UI assets       │
└────────┬───────────────┬────────┘
         │               │
         ▼               ▼
┌─────────────────┐    ┌─────────────────────────────────┐
│    SQLite DB    │    │      Web Monitoring Dashboard   │
│   (SQLAlchemy)  │    │      (Chart.js / Live Polling)  │
└─────────────────┘    └─────────────────────────────────┘
```

------------------------------------------------------------------------

## Hardware Configuration & Pinout

### Bill of Materials

-   ESP32-WROOM-32 Development Board
-   Sharp GP2Y1014AU0F Optical Dust Sensor
-   220 µF electrolytic capacitor
-   150 Ω resistor
-   Solderless breadboard and jumper wires

### Sensor Wiring

  -----------------------------------------------------------------------
  Sensor Pin        Wire Color        ESP32 / Power     Circuit Notes
                                      Connection        
  ----------------- ----------------- ----------------- -----------------
  Pin 1 (V-LED)     White / Red       Connected to 5V   Connected via 150
                                      (VIN / VCC)       Ω resistor;
                                                        buffered to GND
                                                        with 220 µF
                                                        capacitor

  Pin 2 (LED-GND)   Blue / Black      Connected to GND  Sensor optical
                                                        ground

  Pin 3 (LED)       Green / Yellow    Connected to GPIO Digital output
                                      23                driving internal
                                                        IRED pulse

  Pin 4 (S-GND)     Yellow / Black    Connected to GND  System common
                                                        ground

  Pin 5 (Vo)        Black / Blue      Connected to GPIO Analog output
                                      34                sampled by ESP32
                                                        ADC1

  Pin 6 (Vcc)       Red               Connected to 5V   Powers internal
                                      (VIN / VCC)       amplifier and
                                                        phototransistor
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Software Stack

  Layer                        Technology
  ---------------------------- ------------------------------------------------------
  Edge Firmware                C++ / Arduino IDE (`WiFiClientSecure`, `HTTPClient`)
  Backend Framework            FastAPI (Python 3.11 slim)
  Database & ORM               SQLite, SQLAlchemy
  Frontend                     HTML5, CSS3, Vanilla JavaScript, Chart.js
  Containerization & Hosting   Docker, Docker Compose, Render

------------------------------------------------------------------------

## Project Structure

``` text
iot-optical-dust-monitoring-system/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI endpoints, database models, and static mounting
│   └── static/
│       └── index.html       # Chart.js dynamic dashboard with alert indicators
├── data/                    # Volume directory for persistent SQLite database file
├── sketch_oct31a/
│   └── sketch_oct31a.ino    # ESP32 firmware for optical pulse timing and HTTP transmission
├── Dockerfile               # Container build instructions for production
├── docker-compose.yml       # Local multi-container orchestration configuration
├── requirements.txt         # Production backend dependencies
├── .gitignore               # Ignores local databases and temporary test scripts
└── README.md
```
