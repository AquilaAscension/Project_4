import os
import time
import random
import requests
from dotenv import load_dotenv

# Load credentials
load_dotenv()

WRITE_KEY = os.getenv("THINGSPEAK_WRITE_KEY")
TALKBACK_ID = os.getenv("TALKBACK_ID")
TALKBACK_KEY = os.getenv("TALKBACK_API_KEY")

def simulate_environment():
    """Generates realistic fluctuating greenhouse data."""
    # Base values
    base_temp = 24.5
    base_press = 1013.0
    
    # Add random noise
    mock_temp = round(base_temp + random.uniform(-1.5, 2.5), 1)
    mock_press = round(base_press + random.uniform(-5.0, 5.0), 0)
    
    return mock_temp, mock_press

def test_loop():
    print("🚀 Starting Cloud/UI Simulator...")
    print("Press Ctrl+C to stop.")
    print("-" * 40)
    
    try:
        while True:
            temp, press = simulate_environment()
            
            # 1. SEND MOCK DATA TO CLOUD
            update_url = "https://api.thingspeak.com/update"
            payload = {"api_key": WRITE_KEY, "field1": temp, "field2": press}
            
            try:
                res = requests.get(update_url, params=payload, timeout=5)
                if res.status_code == 200:
                    print(f"[DATA SENT] Temp: {temp}°C | Pressure: {press}hPa")
                else:
                    print(f"[ERROR] ThingSpeak returned status: {res.status_code}")
            except Exception as e:
                print(f"[NETWORK ERROR] Failed to send data: {e}")

            # 2. CHECK FOR UI BUTTON PRESSES (TalkBack)
            tb_url = f"https://api.thingspeak.com/talkbacks/{TALKBACK_ID}/commands/execute.json"
            try:
                tb_res = requests.get(tb_url, params={"api_key": TALKBACK_KEY}, timeout=5)
                if tb_res.status_code == 200 and tb_res.text.strip():
                    cmd = tb_res.json().get("command_string")
                    if cmd == "PUMP_ON":
                        print("\n" + "="*40)
                        print("💧 MANUAL OVERRIDE RECEIVED FROM WEBSITE!")
                        print("💧 Action: Triggering Virtual Pump for 5s...")
                        print("="*40 + "\n")
            except Exception as e:
                pass # Fail silently for TalkBack checks

            # 3. WAIT (Respecting the 15-second rate limit)
            print("Waiting 16 seconds for API cooldown...")
            time.sleep(16)

    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped.")

if __name__ == "__main__":
    if not WRITE_KEY:
        print("ERROR: .env file not found or THINGSPEAK_WRITE_KEY is missing.")
    else:
        test_loop()