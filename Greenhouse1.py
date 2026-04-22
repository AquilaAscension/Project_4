import time
import board
import busio
import adafruit_bmp280
import RPi.GPIO as GPIO
from Adafruit_IO import Client

# --- Configuration ---
ADAFRUIT_IO_KEY = 'aio_RGtx41yaA7xGojddFf4OszsND7zK'
ADAFRUIT_IO_USERNAME = 'Kcirtip'

# GPIO Pins
PUMP_PIN = 17 
LED_PIN = 22  # Connect LED to GPIO 22

#Demo Mode to randomize the temp values
DEMO_MODE = True # Set to False for normal operation
demo_temp = 20.0 # Starting point

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.setup(LED_PIN, GPIO.OUT)

# Ensure everything starts OFF
GPIO.output(PUMP_PIN, GPIO.HIGH) # HIGH = OFF (assuming Active Low relay)
GPIO.output(LED_PIN, GPIO.LOW)   # LOW = OFF (assuming Standard LED)

# Setup Sensor with your specific address
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

# Thresholds
HOT_THRESHOLD = 24.6
COLD_THRESHOLD = 24.4

try:
    print("System running...")
    while True:
        temperature = bmp280.temperature
        print(f"Temperature: {temperature:.2f} C")
        

	    if DEMO_MODE:
			demo_temp += 1.0 # Simulate temperature rising
			if demo_temp > 30.0: demo_temp = 10.0 # Reset range
				temperature = demo_temp
		else:
			temperature = bmp280.temperature # Normal operation
        
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
            GPIO.output(PUMP_PIN, GPIO.HIGH)
            GPIO.output(LED_PIN, GPIO.LOW)

        time.sleep(5)

except Exception as e:
    print(f"Error: {e}")

finally:
    # Emergency Shutdown
    print("Shutting down safely.")
    GPIO.output(PUMP_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
