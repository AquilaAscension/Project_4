import time
import board
import busio
import adafruit_bmp280
import RPi.GPIO as GPIO
from Adafruit_IO import Client
import subprocess
import time
from datetime import datetime
import os

# --- Configuration ---
ADAFRUIT_IO_KEY = 'aio_RGtx41yaA7xGojddFf4OszsND7zK'
ADAFRUIT_IO_USERNAME = 'Kcirtip'

# GPIO Pins
PUMP_PIN = 17
LED_PIN = 22  # Connect LED to GPIO 22

# Demo Mode to randomize the temp values
DEMO_MODE = False # Set to False for normal operation
demo_temp = 20.0  # Starting point

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.setup(LED_PIN, GPIO.OUT)

# Ensure everything starts OFF
GPIO.output(PUMP_PIN, GPIO.HIGH)  # HIGH = OFF (assuming Active Low relay)
GPIO.output(LED_PIN, GPIO.LOW)    # LOW = OFF (assuming Standard LED)

# Setup Sensor with your specific address
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

# Thresholds
HOT_THRESHOLD = 24.0
COLD_THRESHOLD = 22.0

# --- Configuration ---
PHOTO_DIR = "/home/pi/greenhouse_photos"
# Create the directory if it doesn't exist
os.makedirs(PHOTO_DIR, exist_ok=True)

# Set the interval (e.g., 3600 seconds = 1 hour)
PHOTO_INTERVAL = 
last_photo_time = 0

def take_photo():
    """Captures a photo using rpicam-still."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = f"{PHOTO_DIR}/plant_{timestamp}.jpg"
    
    # rpicam-still command
    cmd = ["rpicam-still", "-o", filepath, "--width", "1920", "--height", "1080", "--nopreview"]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Photo saved: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"Error capturing image: {e}")
try:
    print("System running...")
    while True:
        temperature = bmp280.temperature
        print(f"Temperature: {temperature:.2f} C")

        if DEMO_MODE:
            demo_temp += 0.2  # Simulate temperature rising
            if demo_temp > 30.0:
                demo_temp = 20.0  # Reset range
            temperature = demo_temp
        else:
            temperature = bmp280.temperature  # Normal operation

        # Send to Cloud
        aio.send('temp', temperature)

        # Logic for HOT (Pump)
        if temperature > HOT_THRESHOLD:
            print("Too hot! Pump ON.")
            GPIO.output(PUMP_PIN, GPIO.LOW)  # Change to HIGH if pump stays OFF
            GPIO.output(LED_PIN, GPIO.LOW)

        # Logic for COLD (LED)
        elif temperature < COLD_THRESHOLD:
            print("Too cold! LED ON.")
            GPIO.output(PUMP_PIN, GPIO.HIGH)
            GPIO.output(LED_PIN, GPIO.HIGH)

        # Logic for "Just Right"
        else:
            print("Temperature is just right!")
            GPIO.output(PUMP_PIN, GPIO.HIGH)
            GPIO.output(LED_PIN, GPIO.LOW)
            
        # --- In your main loop ---
        while True:
        # 1. Read your BMP280/Sensors here...
    
        # 2. Check if it is time to take a photo
            current_time = time.time()
        if current_time - last_photo_time >= PHOTO_INTERVAL:
            take_photo()
            last_photo_time = current_time

        time.sleep(3.5)

except Exception as e:
    print(f"Error: {e}")
finally:
    # Emergency Shutdown
    print("Shutting down safely.")
    GPIO.output(PUMP_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
