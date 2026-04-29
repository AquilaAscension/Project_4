Greenhouse Pro: Autonomous IoT Monitoring & Control System

Greenhouse Pro is a modular Raspberry Pi-based system designed for autonomous plant environment management. It features cloud-synchronized telemetry via ThingSpeak, a local Neumorphic web dashboard, and an asynchronous camera system for live plant monitoring.

## 🚀 Key Features

* **Hybrid Control Logic**: Combines local hardware hysteresis (preventing relay "chatter") with cloud-based manual overrides.
* **Modern Neumorphic UI**: A "Soft UI" dashboard featuring custom gauges, a 15-second sync countdown, and a live photo feed.
* **Asynchronous Monitoring**: Captures high-resolution plant photos (1080p) in the background without interrupting sensor loops or pump timing.
* **Heartbeat Status LED**: Multi-frequency LED patterns communicate system health, errors, and environmental status at a glance.
* **Data Resilience**: Dual-logging system saves data to a local CSV file for offline backup while syncing to the cloud every 16 seconds.

---

## 🛠️ Hardware Mapping

| Component | Pin / Address | Note |
| :--- | :--- | :--- |
| **BMP280 Sensor** | I2C (0x76) | Temperature & Pressure |
| **Water Pump** | GPIO 17 | Relay Controlled (Active Low) |
| **Heartbeat LED** | GPIO 22 | System Status Indicator |
| **Pi Camera** | CSI Port | 1080p Plant Monitoring |

---

## 📁 File Structure

* `main.py`: The central conductor that coordinates sensors, logic, and timing.
* `hardware_control.py`: Low-level drivers for GPIO, BMP280, and the live camera capture pipeline.
* `cloud_service.py`: Handles ThingSpeak API requests, TalkBack command execution, and local CSV logging.
* `index.html`: The modern web-based control center (Neumorphic Design) with live MJPEG camera view.
* `.env`: Configuration file for private API keys and temperature thresholds.

---

## ⚙️ Installation & Setup

### 1. Install Dependencies
Run the following command on your Raspberry Pi:
```bash
pip install requests python-dotenv adafruit-circuitpython-bmp280 RPi.GPIO
```

### 2. Configure Environment Variables
Create a file named `.env` in the project root and add your specific credentials:
```ini
THINGSPEAK_WRITE_KEY=YOUR_WRITE_KEY
THINGSPEAK_READ_KEY=YOUR_READ_KEY
TALKBACK_ID=YOUR_TALKBACK_ID
TALKBACK_API_KEY=YOUR_TALKBACK_API_KEY
HOT_THRESHOLD=25.0
COLD_THRESHOLD=18.0
```

---

## 🏃 How to Run the System

The system requires two concurrent processes to run simultaneously in **two separate terminal windows**.

### Step 1: Start the Logic Brain (Terminal 1)
This handles the sensors, pump logic, camera snapshots, and cloud syncing.
```bash
python3 main.py
```
`main.py` also starts the live camera stream endpoint at `http://<YOUR_PI_IP>:8001/stream.mjpg`.

### Step 2: Start the Web Dashboard (Terminal 2)
This hosts the website so you can access it from your phone or laptop. Navigate to your project folder and run:
```bash
python3 -m http.server 8000
```

---

## 📱 Accessing the Dashboard

1.  **Find your Pi's IP Address**: In a terminal, type `hostname -I`. (Commonly starts with `192.168...`).
2.  **Open a Browser**: On any device (Laptop/Phone) connected to the same Wi-Fi, go to:
    `http://<YOUR_PI_IP>:8000`
3.  **Use the UI**: 
    * The **Progress Bar** at the top shows the 15-second refresh cycle.
    * The **Gauges** show current Greenhouse conditions.
    * The **Camera Feed** displays the Pi camera live stream and falls back to the latest saved photo if streaming is unavailable.
    * The **Pulse Button** sends a command to ThingSpeak that the Pi will execute on its next check.

---

## 📊 System Status Indicators (LED)

| LED Pattern | System Status | Meaning |
| :--- | :--- | :--- |
| **Slow Blink (1s)** | NORMAL | Temperature is within range. |
| **Solid ON** | PUMP ACTIVE | Auto-cooling or Manual Pulse is running. |
| **Fast Blink (0.2s)** | COLD | Temperature is below the Cold Threshold. |
| **Rapid "Panic" Blink** | SENSOR ERROR | BMP280 is disconnected or failing. |

---

## 📝 Project Notes
* **Photo Storage**: Archived photos are stored in `/home/pi/greenhouse_photos`.
* **Web Feed**: The dashboard uses the live MJPEG stream on port `8001` and falls back to `latest_photo.jpg` if the stream is unavailable.
* **Cloud Limit**: ThingSpeak has a 15-second update limit; the UI is designed to respect this via the countdown loader.
```
