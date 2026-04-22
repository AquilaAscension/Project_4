# test_cloud.py
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

WRITE_KEY = os.getenv("THINGSPEAK_WRITE_KEY")
# Verify the key is loading
if not WRITE_KEY:
    print("Error: Write Key not found in .env file!")

def send_test_data(value):
    url = f"https://api.thingspeak.com/update?api_key={WRITE_KEY}&field1={value}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print(f"Success! ThingSpeak entry ID: {r.text}")
        else:
            print(f"Failed. Status Code: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Sending first test point...")
    send_test_data(22.5) # Send a dummy temperature