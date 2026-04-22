import time
from cloud_service import process_logic_and_cloud

# When you merge, replace these with your actual BMP280/GPIO code
def run_greenhouse():
    print("Greenhouse System Online. Press Ctrl+C to exit.")
    try:
        while True:
            # Simulate sensor readings (Replace with bmp280.temperature etc.)
            current_temp = 26.5 
            current_press = 1012.4
            
            # This calls your hysteresis + cloud logic
            pump_status = process_logic_and_cloud(current_temp, current_press)
            
            if pump_status:
                # GPIO.output(17, GPIO.LOW) # Turn on relay
                print("ACTION: PUMP ON")
            else:
                # GPIO.output(17, GPIO.HIGH) # Turn off relay
                pass
                
            time.sleep(2) # Local loop speed
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    run_greenhouse()