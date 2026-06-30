# AI-VISION-MATE-SMART-STICK
Ai Smart Stick For Visually Impaired Person  BSCS FYDP 1 2026
  
  An AI-powered assistive navigation device built for visually impaired
  individuals as part of our BSCS Final Year Design Project 2026.
  
  ## What It Does
  
  The device uses a Raspberry Pi 5 with a Pi Camera to detect objects in
  real time using a YOLOv8 AI model trained on 601 categories. Three
  ultrasonic sensors measure the distance to obstacles on the left, center,
  and right. The system speaks the object name, its direction, and distance
  through Bluetooth earphones. Everything runs offline with no internet.
  
  ## Team
  
  - Umer Manzoor (GL) — AI and ML Developer
  - Mustafa Rehman — Embedded System Developer
  - Noor Fatima — Software and Voice System Developer
  - Safia Naz — Software and Computer Vision Researcher
  
  ## Hardware
  
  - Raspberry Pi 5 (4GB)
  - Pi Camera V2 NoIR (Sony IMX219, 62 degree FOV)
  - 3x HC-SR04 Ultrasonic Sensors (30cm to 400cm range)
  - Push Button (GPIO3)
  - Bluetooth Earphones (AirPods Pro)
  - 20,000mAh Power Bank
  
  ## AI Model
  
  We used the YOLOv8 Nano model pre-trained on Google Open Images V7.
  The model was converted from PyTorch (.pt) to ONNX format which
  increased inference speed from 8 FPS to 52 FPS on the Pi 5 CPU.
  
  - Model: yolov8n-oiv7 (Ultralytics)
  - Dataset: Google Open Images V7 — 9 million images — 601 classes
  - Format: ONNX Runtime for fast inference
  - Speed: 19ms per frame (52 FPS)
  
  ## How to Run
  
  See SETUP.md for full installation instructions.
  
  Quick start:
    python3 src/ai_vision_mate.py
  
  Live camera view on phone browser:
    http://192.168.100.200:8080
  
  ## Button Controls
  
  - Press once while running: Sleep mode
  - Press once while sleeping: Wake up and resume
  - Press twice quickly: Safe shutdown
  
  ## Future Plans
  
  - SOS alert via SMS on triple button press
  - Urdu voice output
  - Custom training on Pakistani environment
  - Hailo AI accelerator for 100+ FPS
  
  ## Acknowledgements
  
  - Ultralytics YOLOv8: github.com/ultralytics/ultralytics
  - Google Open Images V7: storage.googleapis.com/openimages/web
  - ONNX Runtime: onnxruntime.ai
