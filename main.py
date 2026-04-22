import time
import hardware_control as hw
from cloud_service import process_logic_and_cloud

last_blink = 0
blink_interval = 1.0 # Default slow blink

try:
    print("Greenhouse System Online... [04/22 Proposal Version]")
    while True:
        # 1. Get Sensor Data
        temp, press = hw.get_readings()
        
        if temp is None:
            # SENSOR ERROR: Rapid panic blink
            hw.set_actuators(pump_on=False, heartbeat_state='ERROR')
            time.sleep(0.1)
            continue

        # 2. Logic Engine (Hysteresis + Cloud)
        should_pump, status = process_logic_and_cloud(temp, press)

        # 3. LED Behavior Selection
        if should_pump:
            # Pump is active (Auto or Manual) -> Solid LED
            h_state = 'PULSE'
            blink_interval = 0 # Keeps LED on
        elif status == "COLD":
            # Too Cold -> Fast Blink
            h_state = 'NORMAL'
            blink_interval = 0.2
        else:
            # Normal -> Steady Slow Blink
            h_state = 'NORMAL'
            blink_interval = 1.0

        # 4. Update Hardware
        now = time.time()
        if h_state == 'PULSE':
            hw.set_actuators(pump_on=True, heartbeat_state='PULSE')
        elif now - last_blink >= blink_interval:
            hw.set_actuators(pump_on=False, heartbeat_state='NORMAL')
            last_blink = now

        # High-frequency loop for responsive manual override
        time.sleep(0.1) 

except KeyboardInterrupt:
    print("\nShutting down safely.")
finally:
    hw.cleanup_hardware()