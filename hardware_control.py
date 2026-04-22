import board
import busio
import adafruit_bmp280
import RPi.GPIO as GPIO
import time

# Pin Definitions
PUMP_PIN = 17 
LED_PIN = 22  

# Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT, initial=GPIO.HIGH) # Off (Active Low)
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)

# Initialize Sensor (Fixed at 0x76)
i2c = busio.I2C(board.SCL, board.SDA)
try:
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
    sensor_online = True
except Exception as e:
    print(f"Sensor Init Failed: {e}")
    sensor_online = False

def get_readings():
    """Returns (temp, pressure) or (None, None) if sensor fails."""
    global sensor_online
    if not sensor_online:
        # Try a quick re-init if it was offline
        try:
            global bmp280
            bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
            sensor_online = True
        except:
            return None, None
            
    try:
        return round(bmp280.temperature, 2), round(bmp280.pressure, 2)
    except:
        sensor_online = False # Set offline for next attempt
        return None, None

def set_actuators(pump_on, heartbeat_state):
    """
    pump_on: Boolean to control relay
    heartbeat_state: String ('NORMAL', 'ERROR', 'PULSE')
    """
    # 1. Pump Control
    if pump_on:
        GPIO.output(PUMP_PIN, GPIO.LOW)  # ON
    else:
        GPIO.output(PUMP_PIN, GPIO.HIGH) # OFF

    # 2. Heartbeat LED Logic
    if heartbeat_state == 'PULSE':
        GPIO.output(LED_PIN, GPIO.HIGH) # Solid ON
    elif heartbeat_state == 'ERROR':
        # Fast toggle handled by main.py timing
        current_state = GPIO.input(LED_PIN)
        GPIO.output(LED_PIN, not current_state)
    else:
        # Normal Toggle
        current_state = GPIO.input(LED_PIN)
        GPIO.output(LED_PIN, not current_state)

def cleanup_hardware():
    print("Cleaning up GPIO...")
    GPIO.output(PUMP_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()