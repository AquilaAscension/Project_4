import board
import busio
import adafruit_bmp280
import RPi.GPIO as GPIO
import time
import os
import subprocess
from datetime import datetime

# Pin Definitions
PUMP_PIN = 17 
LED_PIN = 22  

# Camera Setup
PHOTO_DIR = "/home/pi/greenhouse_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)
# This is where your script runs, we'll save a web-friendly copy here
WEB_DIR = os.getcwd() 

# Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)

i2c = busio.I2C(board.SCL, board.SDA)
try:
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
    sensor_online = True
except Exception as e:
    print(f"Sensor Init Failed: {e}")
    sensor_online = False

def get_readings():
    global sensor_online
    if not sensor_online:
        try:
            global bmp280
            bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
            sensor_online = True
        except:
            return None, None
            
    try:
        return round(bmp280.temperature, 2), round(bmp280.pressure, 2)
    except:
        sensor_online = False 
        return None, None

def set_actuators(pump_on, heartbeat_state):
    if pump_on:
        GPIO.output(PUMP_PIN, GPIO.LOW)  
    else:
        GPIO.output(PUMP_PIN, GPIO.HIGH) 

    if heartbeat_state == 'PULSE':
        GPIO.output(LED_PIN, GPIO.HIGH) 
    elif heartbeat_state == 'ERROR':
        current_state = GPIO.input(LED_PIN)
        GPIO.output(LED_PIN, not current_state)
    else:
        current_state = GPIO.input(LED_PIN)
        GPIO.output(LED_PIN, not current_state)

def take_photo():
    """Asynchronous camera trigger. Won't freeze the main loop!"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = f"{PHOTO_DIR}/plant_{timestamp}.jpg"
    latest_path = os.path.join(WEB_DIR, "latest_photo.jpg")

    # This command takes the photo, then copies it to 'latest_photo.jpg'
    cmd = f"rpicam-still -o {archive_path} --width 1920 --height 1080 --nopreview && cp {archive_path} {latest_path}"
    
    try:
        # Popen runs the process in the background
        subprocess.Popen(cmd, shell=True)
        print("📸 [CAMERA] Snap triggered in background...")
    except Exception as e:
        print(f"Camera Error: {e}")

def cleanup_hardware():
    print("Cleaning up GPIO...")
    GPIO.output(PUMP_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()