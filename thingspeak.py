import os
import requests
import time
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WRITE_KEY = os.getenv("THINGSPEAK_WRITE_KEY")
TALKBACK_ID = os.getenv("TALKBACK_ID")
TALKBACK_KEY = os.getenv("TALKBACK_API_KEY")
HOT_THRESHOLD = float(os.getenv("HOT_THRESHOLD", 25.0))

HYSTERESIS_OFFSET = 0.5
LOG_FILE = "greenhouse_data.csv"

last_cloud_update = 0
pump_active = False 

def log_locally(temp, pressure):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Temp_C', 'Pressure_hPa'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), temp, pressure])

def process_logic_and_cloud(temp, pressure):
    global last_cloud_update, pump_active
    current_time = time.time()
    manual_pulse = False

    # 1. Automatic Logic
    if temp > HOT_THRESHOLD:
        pump_active = True
    elif temp < (HOT_THRESHOLD - HYSTERESIS_OFFSET):
        pump_active = False

    # 2. Cloud Communication (Every 16s)
    if current_time - last_cloud_update >= 16:
        url = "https://api.thingspeak.com/update"
        payload = {"api_key": WRITE_KEY, "field1": temp, "field2": pressure}
        
        try:
            # Send both fields
            r = requests.get(url, params=payload, timeout=5)
            print(f"Cloud Sync Status: {r.status_code} | Sent T:{temp} P:{pressure}")
            log_locally(temp, pressure)
            last_cloud_update = current_time
        except Exception as e:
            print(f"Cloud Sync Failed: {e}")

        # Check TalkBack
        tb_url = f"https://api.thingspeak.com/talkbacks/{TALKBACK_ID}/commands/execute.json"
        try:
            resp = requests.get(tb_url, params={"api_key": TALKBACK_KEY}, timeout=5)
            if resp.status_code == 200 and resp.text.strip():
                cmd_data = resp.json()
                if cmd_data.get("command_string") == "PUMP_ON":
                    print("!!! MANUAL PULSE RECEIVED FROM CLOUD !!!")
                    manual_pulse = True
        except:
            pass

    return pump_active or manual_pulse