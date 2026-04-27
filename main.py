import time
import hardware_control as hw
from cloud_service import process_logic_and_cloud

last_blink = 0
blink_interval = 1.0 

# Camera Timing
last_photo = 0
PHOTO_INTERVAL = 60 # Take a picture every 60 seconds

try:
    print("Greenhouse System Online... [Camera Active]")
    while True:
        now = time.time()

        # --- CAMERA LOGIC ---
        if now - last_photo >= PHOTO_INTERVAL:
            hw.take_photo()
            last_photo = now

        # --- SENSOR & CLOUD LOGIC ---
        temp, press = hw.get_readings()
        
        if temp is None:
            hw.set_actuators(pump_on=False, heartbeat_state='ERROR')
            time.sleep(0.1)
            continue

        should_pump, status = process_logic_and_cloud(temp, press)

        # --- LED LOGIC ---
        if should_pump:
            h_state = 'PULSE'
            blink_interval = 0 
        elif status == "COLD":
            h_state = 'NORMAL'
            blink_interval = 0.2
        else:
            h_state = 'NORMAL'
            blink_interval = 1.0

        if h_state == 'PULSE':
            hw.set_actuators(pump_on=True, heartbeat_state='PULSE')
        elif now - last_blink >= blink_interval:
            hw.set_actuators(pump_on=False, heartbeat_state='NORMAL')
            last_blink = now

        time.sleep(0.1) 

except KeyboardInterrupt:
    print("\nShutting down safely.")
finally:
    hw.cleanup_hardware()