import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import hardware_control as hw
from cloud_service import process_logic_and_cloud

last_blink = 0
blink_interval = 1.0 

# Camera Timing
last_photo = 0
PHOTO_INTERVAL = 60 # Take a picture every 60 seconds
STREAM_PORT = 8001

class CameraStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] != "/stream.mjpg":
            self.send_error(404)
            return

        frame_bytes, last_frame_timestamp = hw.get_latest_frame(timeout=3.0)
        if frame_bytes is None:
            self.send_error(503, "Camera frame unavailable")
            return

        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        try:
            while True:
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame_bytes)}\r\n\r\n".encode())
                self.wfile.write(frame_bytes)
                self.wfile.write(b"\r\n")
                self.wfile.flush()

                next_frame_bytes, frame_timestamp = hw.get_latest_frame(
                    after_timestamp=last_frame_timestamp,
                    timeout=5.0,
                )
                if next_frame_bytes is not None:
                    frame_bytes = next_frame_bytes
                    last_frame_timestamp = frame_timestamp
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    def log_message(self, format, *args):
        return

def start_camera_server():
    if not hw.start_camera_stream():
        print("Live camera stream unavailable; dashboard will use snapshots.")
        return None

    try:
        server = ThreadingHTTPServer(("0.0.0.0", STREAM_PORT), CameraStreamHandler)
    except OSError as e:
        print(f"Camera stream server failed to start: {e}")
        return None

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"Camera stream serving at http://<pi-ip>:{STREAM_PORT}/stream.mjpg")
    return server

camera_server = start_camera_server()

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
    if camera_server is not None:
        camera_server.shutdown()
        camera_server.server_close()
    hw.cleanup_hardware()
