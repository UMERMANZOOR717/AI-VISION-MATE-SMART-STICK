import os
import sys
import time
import threading
import lgpio
import cv2
import numpy as np
from flask import Flask, Response
from ultralytics import YOLO
from picamera2 import Picamera2

onnx_path  = '/home/aivisionmate/yolov8n-oiv7.onnx'
pt_path    = '/home/aivisionmate/yolov8n-oiv7.pt'
model_path = onnx_path if os.path.exists(onnx_path) else pt_path

CONF         = 0.55
IMGSZ        = 160
NEED         = 5
MAX_OBJ      = 2
MIN_BOX      = 0.05
CAM_W        = 320
CAM_H        = 240
MIN_DIST     = 30
MAX_DIST     = 400
SMOOTH       = 7
SOUND_SPD    = 34900
DANGER_DELAY = 2.5
NORMAL_DELAY = 4.0

BTN    = 3
TRIG_C = 17
ECHO_C = 27
TRIG_L = 23
ECHO_L = 24
TRIG_R = 5
ECHO_R = 6

sensors = {
    'center': (TRIG_C, ECHO_C),
    'left':   (TRIG_L, ECHO_L),
    'right':  (TRIG_R, ECHO_R),
}

try:
    gpio = lgpio.gpiochip_open(0)
    for p in [TRIG_C, ECHO_C, TRIG_L, ECHO_L, TRIG_R, ECHO_R, BTN]:
        try:
            lgpio.gpio_free(gpio, p)
        except:
            pass
    for trig, echo in sensors.values():
        lgpio.gpio_claim_output(gpio, trig)
        lgpio.gpio_claim_input(gpio, echo)
    lgpio.gpio_claim_input(gpio, BTN, lgpio.SET_PULL_UP)
    print("gpio ready")
except Exception as e:
    print("gpio failed:", e)
    sys.exit(1)

danger_labels = {
    "Person", "Human face", "Human body", "Human hand", "Human head",
    "Man", "Woman", "Boy", "Girl",
    "Car", "Truck", "Bus", "Van", "Motorcycle", "Bicycle",
    "Vehicle", "Ambulance", "Taxi", "Train",
    "Dog", "Horse", "Cattle", "Bear", "Elephant", "Snake",
    "Fire", "Stairs", "Door", "Ladder",
}

def cm_to_speech(cm):
    if not cm:
        return ""
    cm = round(cm)
    if cm < 100:
        r = max(10, round(cm / 10) * 10)
        return f"{int(r)} centimeters"
    m = cm / 100
    if m < 2.0:
        return f"{round(m * 10) / 10:.1f} meters"
    r = round(m * 2) / 2
    return f"{int(r)} meters" if r == int(r) else f"{r:.1f} meters"

def get_bt_sink():
    try:
        s = os.popen(
            "pactl list sinks short 2>/dev/null | grep bluez | head -1 | awk '{print $2}'"
        ).read().strip()
        return s if s else None
    except:
        return None

def set_volume():
    try:
        sink = get_bt_sink()
        if sink:
            os.system(f'pactl set-default-sink {sink} 2>/dev/null')
            os.system(f'pactl set-sink-volume {sink} 100% 2>/dev/null')
            os.system(f'pactl set-sink-mute {sink} 0 2>/dev/null')
        os.system('pactl set-sink-volume @default@ 100% 2>/dev/null')
        os.system('amixer set Master 100% 2>/dev/null')
    except:
        pass

def load_mac():
    try:
        if os.path.exists('/home/aivisionmate/bt_mac.txt'):
            with open('/home/aivisionmate/bt_mac.txt') as f:
                return f.read().strip()
    except:
        pass
    return None

def do_connect(mac):
    os.system(f'bluetoothctl trust {mac} 2>/dev/null')
    os.system(f'bluetoothctl connect {mac} 2>/dev/null')
    time.sleep(4)
    ok = os.popen(
        f'bluetoothctl info {mac} 2>/dev/null | grep "Connected: yes"'
    ).read().strip()
    return bool(ok)

def initial_connect():
    os.system('bluetoothctl power on 2>/dev/null')
    os.system('bluetoothctl agent on 2>/dev/null')
    os.system('bluetoothctl default-agent 2>/dev/null')
    saved = load_mac()
    if saved:
        if do_connect(saved):
            time.sleep(2)
            set_volume()
            print("bluetooth connected:", saved)
            return
    os.system('timeout 12 bluetoothctl scan on 2>/dev/null')
    time.sleep(12)
    devs = os.popen(
        "bluetoothctl devices 2>/dev/null | awk '{print $2}'"
    ).read().strip().split('\n')
    for mac in devs:
        mac = mac.strip()
        if not mac or len(mac) < 17:
            continue
        os.system(f'bluetoothctl pair {mac} 2>/dev/null')
        if do_connect(mac):
            time.sleep(2)
            set_volume()
            with open('/home/aivisionmate/bt_mac.txt', 'w') as f:
                f.write(mac)
            print("bluetooth connected:", mac)
            return

def bt_watchdog():
    while True:
        time.sleep(15)
        try:
            if not get_bt_sink():
                mac = load_mac()
                if mac:
                    do_connect(mac)
                    time.sleep(3)
                    set_volume()
        except:
            pass

def volume_keepalive():
    while True:
        time.sleep(10)
        set_volume()

threading.Thread(target=initial_connect, daemon=True).start()
threading.Thread(target=bt_watchdog, daemon=True).start()
threading.Thread(target=volume_keepalive, daemon=True).start()

voice_lock = threading.Lock()

def say(text, speed=145):
    set_volume()
    os.system(f'espeak -s {speed} "{text}" 2>/dev/null')

def speak(text, speed=162):
    def run():
        if not voice_lock.acquire(blocking=False):
            return
        try:
            set_volume()
            os.system(f'espeak -s {speed} "{text}" 2>/dev/null')
            print("speak:", text)
        finally:
            voice_lock.release()
    threading.Thread(target=run, daemon=True).start()

os.system('xset s off 2>/dev/null')
os.system('xset -dpms 2>/dev/null')
os.system('xset s noblank 2>/dev/null')
set_volume()

print("loading model:", model_path)
try:
    model  = YOLO(model_path, task='detect')
    labels = model.names
    dummy  = np.zeros((CAM_H, CAM_W, 3), dtype=np.uint8)
    for _ in range(3):
        model(dummy, conf=CONF, verbose=False, imgsz=IMGSZ)
    t0 = time.time()
    for _ in range(5):
        model(dummy, conf=CONF, verbose=False, imgsz=IMGSZ)
    ms  = (time.time() - t0) / 5 * 1000
    fps = 1000 / ms
    print(f"model ready {ms:.0f}ms ~{fps:.0f} fps")
except Exception as e:
    print("model failed:", e)
    sys.exit(1)

def open_camera():
    try:
        cam = Picamera2()
        cam.configure(cam.create_preview_configuration(
            main={"size": (CAM_W, CAM_H)}
        ))
        cam.start()
        time.sleep(1)
        return cam
    except Exception as e:
        print("camera error:", e)
        return None

picam = open_camera()
if not picam:
    say("Camera not found")
    sys.exit(1)

current_frame = [None]
annotated_jpg = [None]
frame_lock    = threading.Lock()
jpg_lock      = threading.Lock()
cam_on        = [True]

def grab_frames():
    global picam
    while cam_on[0]:
        try:
            f = picam.capture_array()
            f = cv2.cvtColor(f, cv2.COLOR_RGB2BGR)
            with frame_lock:
                current_frame[0] = f
        except:
            try:
                picam.stop()
            except:
                pass
            time.sleep(2)
            picam = open_camera()

threading.Thread(target=grab_frames, daemon=True).start()

def get_frame():
    with frame_lock:
        f = current_frame[0]
        return f.copy() if f is not None else None

current_dist = {'left': None, 'center': None, 'right': None}
d_lock       = threading.Lock()
d_buffers    = {'left': [], 'center': [], 'right': []}

def ping(trig, echo):
    try:
        lgpio.gpio_write(gpio, trig, 0)
        time.sleep(0.01)
        lgpio.gpio_write(gpio, trig, 1)
        time.sleep(0.00001)
        lgpio.gpio_write(gpio, trig, 0)
        deadline = time.time() + 0.04
        ps = time.time()
        while lgpio.gpio_read(gpio, echo) == 0:
            ps = time.time()
            if time.time() > deadline:
                return None
        deadline = time.time() + 0.04
        pe = time.time()
        while lgpio.gpio_read(gpio, echo) == 1:
            pe = time.time()
            if time.time() > deadline:
                break
        cm = round((pe - ps) * (SOUND_SPD / 2), 1)
        return cm if MIN_DIST <= cm <= MAX_DIST else None
    except:
        return None

def poll_sensors():
    while True:
        for name, (trig, echo) in sensors.items():
            cm  = ping(trig, echo)
            buf = d_buffers[name]
            if cm is not None:
                buf.append(cm)
                if len(buf) > SMOOTH:
                    buf.pop(0)
                s   = sorted(buf)
                n   = len(s)
                med = s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2
                with d_lock:
                    current_dist[name] = round(med)
            else:
                if buf:
                    buf.pop(0)
                if not buf:
                    with d_lock:
                        current_dist[name] = None
            time.sleep(0.025)

threading.Thread(target=poll_sensors, daemon=True).start()

def distances():
    with d_lock:
        return dict(current_dist)

def do_shutdown():
    say("Shutting down goodbye", 145)
    time.sleep(2)
    cam_on[0] = False
    try:
        picam.stop()
    except:
        pass
    try:
        lgpio.gpiochip_close(gpio)
    except:
        pass
    os.system("sudo shutdown -h now")

asleep         = False
btn_count      = 0
last_press     = 0
btn_timer      = [None]
btn_last_state = [False]

def handle_button():
    global btn_count, asleep
    n         = btn_count
    btn_count = 0
    if n == 1:
        if not asleep:
            asleep = True
            say("Going to sleep. Press button to wake up", 145)
        else:
            asleep = False
            say("Waking up. Start detection", 145)
    elif n >= 2:
        say("Shutting down goodbye", 145)
        time.sleep(1)
        do_shutdown()

def poll_button():
    global btn_count, last_press
    try:
        pressed = lgpio.gpio_read(gpio, BTN) == 0
        if pressed and not btn_last_state[0]:
            now = time.time()
            if now - last_press > 0.3:
                btn_count += 1
                last_press = now
                if btn_timer[0]:
                    btn_timer[0].cancel()
                btn_timer[0] = threading.Timer(1.2, handle_button)
                btn_timer[0].start()
        btn_last_state[0] = pressed
    except:
        pass

flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Vision Mate</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background:#111;
    display:flex;
    flex-direction:column;
    align-items:center;
    font-family:Arial,sans-serif;
    padding:8px;
  }
  h3   { color:#00cc88; font-size:15px; margin:6px 0; }
  img  { width:100%; max-width:640px; border:2px solid #00cc88; border-radius:6px; }
  p    { color:#888; font-size:11px; margin:5px 0; }
  .dot {
    display:inline-block; width:8px; height:8px;
    background:#00cc88; border-radius:50%; margin-right:5px;
    animation:blink 1s infinite;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
</style>
</head>
<body>
<h3><span class="dot"></span>AI Vision Mate — Live Detection</h3>
<img src="/video">
<p>Green = safe &nbsp;|&nbsp; Red = danger &nbsp;|&nbsp; AI VISION MATE 2026</p>
</body>
</html>'''

@flask_app.route('/video')
def video():
    def gen():
        while True:
            with jpg_lock:
                jpg = annotated_jpg[0]
            if jpg:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                       + jpg + b'\r\n')
            time.sleep(0.04)
    return Response(gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

threading.Thread(
    target=lambda: flask_app.run(
        host='0.0.0.0', port=8080,
        threaded=True, use_reloader=False
    ),
    daemon=True
).start()
print("stream: http://192.168.100.200:8080")

time.sleep(10)
set_volume()
say("Welcome to AI Vision Mate Smart Stick", 138)
time.sleep(0.3)
say("Start detection", 138)

print(f"running {fps:.0f} fps | camera detection only | AI VISION MATE")

seen_counts = {}
last_spoken = {}
fps_count   = 0
fps_t       = time.time()
crashes     = 0

while True:
    try:
        while True:
            poll_button()

            if asleep:
                time.sleep(0.05)
                continue

            frame = get_frame()
            if frame is None:
                continue

            d   = distances()
            now = time.time()

            fps_count += 1
            if now - fps_t >= 5.0:
                print(
                    f"fps={fps_count/(now-fps_t):.0f} "
                    f"L={d['left']} C={d['center']} R={d['right']}"
                )
                fps_count = 0
                fps_t     = now

            try:
                results = model(frame, conf=CONF, verbose=False, imgsz=IMGSZ)
            except:
                continue

            web_frame = frame.copy()
            detected  = set()

            for r in results:
                boxes = sorted(
                    r.boxes, key=lambda b: float(b.conf), reverse=True
                )[:MAX_OBJ]

                for box in boxes:
                    box_w = float(box.xywh[0][2])
                    if box_w < CAM_W * MIN_BOX:
                        continue

                    cid  = int(box.cls)
                    conf = float(box.conf)
                    name = labels.get(cid, "object")
                    detected.add(name)

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    color = (0, 0, 255) if name in danger_labels else (0, 220, 100)
                    cv2.rectangle(web_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        web_frame, f"{name} {conf:.0%}",
                        (x1, max(y1 - 6, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
                    )

                    seen_counts[name] = seen_counts.get(name, 0) + 1
                    if seen_counts[name] < NEED:
                        continue

                    x = float(box.xywh[0][0])
                    if x < CAM_W / 3:
                        position = "on your left"
                        sensor   = "left"
                    elif x > CAM_W * 2 / 3:
                        position = "on your right"
                        sensor   = "right"
                    else:
                        position = "in front"
                        sensor   = "center"

                    dist_str = cm_to_speech(d[sensor])
                    message  = (
                        f"{name} {position} {dist_str}"
                        if dist_str else
                        f"{name} {position}"
                    )
                    elapsed = now - last_spoken.get(name, 0)

                    if name in danger_labels:
                        if elapsed > DANGER_DELAY:
                            speak(f"Warning {message}", 160)
                            last_spoken[name] = now
                            print(f"danger: {name} {conf:.0%} {position} {d[sensor]}cm")
                    else:
                        if elapsed > NORMAL_DELAY:
                            speak(message, 150)
                            last_spoken[name] = now
                            print(f"detect: {name} {conf:.0%} {position} {d[sensor]}cm")

            cv2.putText(
                web_frame,
                f"FPS:{int(fps_count/max(now-fps_t,1))}  L:{d['left']} C:{d['center']} R:{d['right']}",
                (4, 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 220, 0), 1
            )

            _, jpg = cv2.imencode('.jpg', web_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            with jpg_lock:
                annotated_jpg[0] = jpg.tobytes()

            for name in list(seen_counts):
                if name not in detected:
                    seen_counts[name] = 0

    except KeyboardInterrupt:
        print("stopped")
        say("Stopped")
        cam_on[0] = False
        try:
            picam.stop()
        except:
            pass
        lgpio.gpiochip_close(gpio)
        sys.exit(0)

    except Exception as e:
        crashes += 1
        print(f"error crash {crashes}:", e)
        seen_counts = {}
        last_spoken = {}
        time.sleep(1)
