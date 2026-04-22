import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# Config
WRITE_KEY = os.getenv("THINGSPEAK_WRITE_KEY")
TALKBACK_ID = os.getenv("TALKBACK_ID")
TALKBACK_KEY = os.getenv("TALKBACK_API_KEY")

last_update_time = 0

def sync_with_cloud(temp, pressure):
    """
    1. Uploads Temp and Pressure to Fields 1 & 2.
    2. Checks TalkBack for any 'Manual Override' commands.
    """
    global last_update_time
    current_time = time.time()
    command_to_execute = None

    # 1. UPLOAD DATA (Every 15s limit)
    if current_time - last_update_time >= 16:
        url = "https://api.thingspeak.com/update"
        params = {
            "api_key": WRITE_KEY,
            "field1": temp,
            "field2": pressure
        }
        try:
            requests.get(url, params=params)
            last_update_time = current_time
            print(f"Cloud Sync: {temp}C, {pressure}hPa")
        except Exception as e:
            print(f"Upload Error: {e}")

    # 2. CHECK FOR COMMANDS (Manual Override)
    # This checks if the website put a command in the queue
    tb_url = f"https://api.thingspeak.com/talkbacks/{TALKBACK_ID}/commands/execute.json"
    tb_params = {"api_key": TALKBACK_KEY}
    
    try:
        response = requests.get(tb_url, params=tb_params)
        if response.status_code == 200 and response.text != "":
            cmd_data = response.json()
            command_to_execute = cmd_data.get("command_string")
            print(f"Received Cloud Command: {command_to_execute}")
    except Exception as e:
        print(f"TalkBack Error: {e}")

    return command_to_execute # Returns 'PUMP_ON', 'PUMP_OFF', or None