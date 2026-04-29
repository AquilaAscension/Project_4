import os
import requests
import time
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Config from .env
WRITE_KEY = os.getenv("THINGSPEAK_WRITE_KEY")
TALKBACK_ID = os.getenv("TALKBACK_ID")
TALKBACK_KEY = os.getenv("TALKBACK_API_KEY")

# Thresholds with Hysteresis
HOT_THRESHOLD = float(os.getenv("HOT_THRESHOLD", 25.0))
COLD_THRESHOLD = float(os.getenv("COLD_THRESHOLD", 18.0))
HYSTERESIS_OFFSET = 0.5

LOG_FILE = "greenhouse_data.csv"
last_cloud_update = 0
pump_active = False
manual_pulse_until = 0
MANUAL_PULSE_SECONDS = 5

def log_locally(temp, pressure):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Temp_C', 'Pressure_hPa'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), temp, pressure])

def process_logic_and_cloud(temp, pressure):
    global last_cloud_update, pump_active, manual_pulse_until
    current_time = time.time()
    manual_pulse = current_time < manual_pulse_until
    system_status = "NORMAL"

    # 1. Automatic Control Logic (Hysteresis)
    if temp > HOT_THRESHOLD:
        pump_active = True
    elif temp < (HOT_THRESHOLD - HYSTERESIS_OFFSET):
        pump_active = False

    # 2. Status Determination
    if temp < COLD_THRESHOLD:
        system_status = "COLD"
    elif pump_active:
        system_status = "HOT"

    # 3. Cloud Communication (Every 16s)
    if current_time - last_cloud_update >= 16:
        url = "https://api.thingspeak.com/update"
        payload = {"api_key": WRITE_KEY, "field1": temp, "field2": pressure}
        
        try:
            r = requests.get(url, params=payload, timeout=5)
            log_locally(temp, pressure)
            last_cloud_update = current_time
        except Exception as e:
            print(f"Cloud Sync Failed: {e}")

        # Check TalkBack for Manual Pulse
        tb_url = f"https://api.thingspeak.com/talkbacks/{TALKBACK_ID}/commands/execute.json"
        try:
            resp = requests.get(tb_url, params={"api_key": TALKBACK_KEY}, timeout=5)
            if resp.status_code == 200 and resp.text.strip():
                if resp.json().get("command_string") == "PUMP_ON":
                    print("!!! MANUAL PULSE TRIGGERED !!!")
                    manual_pulse_until = current_time + MANUAL_PULSE_SECONDS
                    manual_pulse = True
        except:
            pass

    # We return: should the pump run, and what is the environmental status
    return (pump_active or manual_pulse), system_status
