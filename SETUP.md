  # Setup Guide — AI Vision Mate Smart Stick
  Noor Fatima — Software and Voice System Developer
  
  This guide covers full installation on Raspberry Pi 5.
  
  ## System Requirements
  
  - Raspberry Pi 5 with 4GB RAM
  - Raspberry Pi OS 64-bit (Bookworm)
  - Pi Camera V2 NoIR connected via CSI port
  - 3x HC-SR04 sensors wired as per wiring_notes.txt
  - Any Bluetooth audio device (AirPods recommended)
  
  ## Step 1 — Update System
  
    sudo apt update && sudo apt upgrade -y
  
  ## Step 2 — Install Libraries
  
    sudo apt install python3-picamera2 python3-opencv python3-lgpio
    sudo apt install espeak pulseaudio pulseaudio-module-bluetooth bluez -y
    pip3 install ultralytics onnxruntime onnx onnxslim flask --break-system-packages
  
  ## Step 3 — Download AI Model
  
    mkdir -p /home/aivisionmate
    cd /home/aivisionmate
    python3 -c "from ultralytics import YOLO; YOLO('yolov8n-oiv7.pt')"
  
  ## Step 4 — Convert Model to ONNX (for 52 FPS)
  
    python3 -c "
    from ultralytics import YOLO
    YOLO('/home/aivisionmate/yolov8n-oiv7.pt').export(
        format='onnx', imgsz=160, simplify=True, opset=12)
    "
  
  ## Step 5 — Copy Project Code
  
    cp src/ai_vision_mate.py /home/aivisionmate/
  
  ## Step 6 — Pair Bluetooth Device
  
    bluetoothctl
    power on
    agent on
    scan on
    pair XX:XX:XX:XX:XX:XX
    trust XX:XX:XX:XX:XX:XX
    connect XX:XX:XX:XX:XX:XX
    exit
    Save the MAC address:
    echo 'XX:XX:XX:XX:XX:XX' > /home/aivisionmate/bt_mac.txt
  
  ## Step 7 — Set Fixed IP Address
  
    nmcli con mod 'YOUR_WIFI' ipv4.addresses 192.168.100.200/24
    nmcli con mod 'YOUR_WIFI' ipv4.gateway 192.168.100.1
    nmcli con mod 'YOUR_WIFI' ipv4.dns 8.8.8.8
    nmcli con mod 'YOUR_WIFI' ipv4.method manual
    nmcli con up 'YOUR_WIFI'
  
  ## Step 8 — Set Up Auto Boot Service
  
    sudo nano /etc/systemd/system/aivisionmate.service
  
    Paste the following content:
  
    [Unit]
    Description=AI Vision Mate Smart Stick
    After=network.target sound.target bluetooth.target
  
    [Service]
    Type=simple
    User=aivisionmate
    WorkingDirectory=/home/aivisionmate
    ExecStart=/usr/bin/python3 /home/aivisionmate/ai_vision_mate.py
    Restart=always
    RestartSec=5
  
    [Install]
    WantedBy=multi-user.target
    Then run:
    sudo systemctl daemon-reload
    sudo systemctl enable aivisionmate.service
    sudo reboot
  
  ## Troubleshooting
  
  GPIO busy error    -->  sudo killall python3 && sleep 3
  No BT audio        -->  pactl list sinks short | grep bluez
  Wrong IP           -->  hostname -I  then recheck nmcli
  Low FPS            -->  vcgencmd get_throttled  (should show 0x0)
  Camera not found   -->  vcgencmd get_camera
