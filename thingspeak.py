import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

WRITE_KEY = os.getenv("THINGSPEAK_WRITE_KEY")
BASE_URL = "https://api.thingspeak.com/update"

last_update_time = 0

def upload_to_thingspeak(temp):
    global last_update_time
    current_time = time.time()
    
    # ThingSpeak 15-second rate limit check
    if current_time - last_update_time < 16:
        print("Cloud skip: Rate limit (15s)")
        return False

    params = {"api_key": WRITE_KEY, "field1": temp}
    try:
        r = requests.get(BASE_URL, params=params)
        if r.status_code == 200:
            print(f"Cloud Update Success: {temp}")
            last_update_time = current_time
            return True
    except Exception as e:
        print(f"Cloud Error: {e}")
        return False

if __name__ == "__main__":
    # Test Standalone
    upload_to_thingspeak(23.5)