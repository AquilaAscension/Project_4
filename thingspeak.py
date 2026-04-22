import os
import requests
import time
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration from .env
WRITE_KEY = os.getenv("THINGSPEAK_WRITE_KEY")
TALKBACK_ID = os.getenv("TALKBACK_ID")
TALKBACK_KEY = os.getenv("TALKBACK_API_KEY")
HOT_THRESHOLD = float(os.getenv("HOT_THRESHOLD", 25.0))

# Hysteresis Constant (Turn off when 0.5 degrees below threshold)
HYSTERESIS_OFFSET = 0.5
LOG_FILE = "greenhouse_data.csv"

last_cloud_update = 0
pump_active = False # Tracks the state for Hysteresis

def log_locally(temp, pressure):
    """Saves data to a CSV file for offline backup."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Temp_C', 'Pressure_hPa'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), temp, pressure])

def process_logic_and_cloud(temp, pressure):
    """
    Handles Hysteresis, Cloud Sync, and Manual Pulse logic.
    Returns: (bool) pump_should_be_on
    """
    global last_cloud_update, pump_active
    current_time = time.time()
    manual_pulse = False

    # 1. HYSTERESIS LOGIC (Automatic Control)
    if temp > HOT_THRESHOLD:
        pump_active = True
    elif temp < (HOT_THRESHOLD - HYSTERESIS_OFFSET):
        pump_active = False

    # 2. CLOUD SYNC & TALKBACK (Every 16 seconds)
    if current_time - last_cloud_update >= 16:
        # Upload Data
        url = "https://api.thingspeak.com/update"
        try:
            requests.get(url, params={"api_key": WRITE_KEY, "field1": temp, "field2": pressure}, timeout=5)
            log_locally(temp, pressure)
            last_cloud_update = current_time
        except Exception as e:
            print(f"Cloud Sync Failed: {e}")

        # Check TalkBack for Manual Pulse
        tb_url = f"https://api.thingspeak.com/talkbacks/{TALKBACK_ID}/commands/execute.json"
        try:
            resp = requests.get(tb_url, params={"api_key": TALKBACK_KEY}, timeout=5)
            if resp.status_code == 200 and resp.text.strip():
                cmd = resp.json().get("command_string")
                if cmd == "PUMP_ON":
                    print("MANUAL PULSE TRIGGERED")
                    manual_pulse = True
        except:
            pass

    # Return True if EITHER automatic hysteresis OR manual pulse is active
    return pump_active or manual_pulse

# --- Example of how this will be called in the main script ---
# if __name__ == "__main__":
#    should_pump = process_logic_and_cloud(26.0, 1013.2)
#    if should_pump:
#        trigger_relay_pulse()