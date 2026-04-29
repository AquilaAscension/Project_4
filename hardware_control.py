import board
import busio
import adafruit_bmp280
import RPi.GPIO as GPIO
import time
import os
import subprocess
import shutil
import threading
from datetime import datetime

# Pin Definitions
PUMP_PIN = 17 
LED_PIN = 22  

# Camera Setup
PHOTO_DIR = "/home/pi/greenhouse_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_PHOTO_PATH = os.path.join(WEB_DIR, "latest_photo.jpg")
STREAM_WIDTH = 960
STREAM_HEIGHT = 540
STREAM_FPS = 10
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"
STREAM_CAMERA_CMD = next(
    (cmd for cmd in ("rpicam-vid", "libcamera-vid") if shutil.which(cmd)),
    None,
)
SNAPSHOT_CAMERA_CMD = next(
    (cmd for cmd in ("rpicam-still", "libcamera-still") if shutil.which(cmd)),
    None,
)

_latest_frame = None
_latest_frame_timestamp = 0.0
_frame_condition = threading.Condition()
_camera_process = None
_camera_thread = None

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

def _set_latest_frame(frame_bytes):
    global _latest_frame, _latest_frame_timestamp
    with _frame_condition:
        _latest_frame = frame_bytes
        _latest_frame_timestamp = time.time()
        _frame_condition.notify_all()

def _capture_camera_frames():
    buffer = bytearray()

    while _camera_process and _camera_process.stdout:
        chunk = _camera_process.stdout.read(4096)
        if not chunk:
            break

        buffer.extend(chunk)
        while True:
            start = buffer.find(JPEG_SOI)
            if start == -1:
                if len(buffer) > 2:
                    del buffer[:-2]
                break

            if start > 0:
                del buffer[:start]

            end = buffer.find(JPEG_EOI, 2)
            if end == -1:
                break

            frame = bytes(buffer[:end + 2])
            del buffer[:end + 2]
            _set_latest_frame(frame)

    if _camera_process:
        return_code = _camera_process.poll()
        if return_code not in (None, 0):
            print(f"Camera stream stopped with code {return_code}.")

def start_camera_stream():
    global _camera_process, _camera_thread

    if _camera_thread and _camera_thread.is_alive():
        return True

    if STREAM_CAMERA_CMD is None:
        print("Camera stream command not found.")
        return False

    cmd = [
        STREAM_CAMERA_CMD,
        "-t",
        "0",
        "--codec",
        "mjpeg",
        "--width",
        str(STREAM_WIDTH),
        "--height",
        str(STREAM_HEIGHT),
        "--framerate",
        str(STREAM_FPS),
        "--nopreview",
        "-o",
        "-",
    ]

    try:
        _camera_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
    except Exception as e:
        print(f"Camera stream failed to start: {e}")
        _camera_process = None
        return False

    _camera_thread = threading.Thread(target=_capture_camera_frames, daemon=True)
    _camera_thread.start()
    print("Camera stream started for live feed.")
    return True

def get_latest_frame(after_timestamp=None, timeout=0.0):
    deadline = time.time() + timeout

    with _frame_condition:
        while True:
            has_newer_frame = _latest_frame is not None and (
                after_timestamp is None or _latest_frame_timestamp > after_timestamp
            )
            if has_newer_frame:
                return _latest_frame, _latest_frame_timestamp

            if timeout <= 0:
                return None, _latest_frame_timestamp

            remaining = deadline - time.time()
            if remaining <= 0:
                return None, _latest_frame_timestamp

            _frame_condition.wait(timeout=remaining)

def _write_jpeg(path, frame_bytes):
    temp_path = f"{path}.tmp"
    with open(temp_path, "wb") as output_file:
        output_file.write(frame_bytes)
    os.replace(temp_path, path)

def _capture_snapshot_fallback(archive_path):
    if SNAPSHOT_CAMERA_CMD is None:
        print("Snapshot command not found.")
        return False

    cmd = [
        SNAPSHOT_CAMERA_CMD,
        "--nopreview",
        "--width",
        "1920",
        "--height",
        "1080",
        "-o",
        archive_path,
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.copyfile(archive_path, LATEST_PHOTO_PATH)
        print("Camera snapshot saved using fallback capture.")
        return True
    except Exception as e:
        print(f"Camera snapshot failed: {e}")
        return False

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
    """Save the most recent streamed frame for the dashboard and archive."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = f"{PHOTO_DIR}/plant_{timestamp}.jpg"
    frame_bytes, _ = get_latest_frame(timeout=2.0)

    if frame_bytes is not None:
        try:
            _write_jpeg(archive_path, frame_bytes)
            _write_jpeg(LATEST_PHOTO_PATH, frame_bytes)
            print(f"Camera snapshot saved: {archive_path}")
            return True
        except Exception as e:
            print(f"Camera snapshot write failed: {e}")
            return False

    return _capture_snapshot_fallback(archive_path)

def cleanup_hardware():
    print("Cleaning up GPIO...")
    if _camera_process and _camera_process.poll() is None:
        _camera_process.terminate()
        try:
            _camera_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _camera_process.kill()

    GPIO.output(PUMP_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
