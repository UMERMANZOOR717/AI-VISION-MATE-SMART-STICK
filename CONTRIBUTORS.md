  # Team Contributions — AI Vision Mate Smart Stick
  BSCS Final Year Design Project 2026
  Iqra University Karachi
  
  ## Umer Manzoor — Group Leader and AI & ML Developer
  
  Umer led the team and handled everything related to the AI model.
  He researched available datasets and selected Google Open Images V7
  with 601 categories as the best option for navigation assistance.
  He downloaded the YOLOv8 Nano model from Ultralytics, exported it
  from PyTorch to ONNX format which increased speed from 8 FPS to
  52 FPS on the Raspberry Pi 5 CPU. He tuned the detection settings
  including confidence threshold, frame confirmation count, and minimum
  box size to reduce false positives. He designed the overall project
  architecture including the threading model that runs camera, sensors,
  voice, and web stream simultaneously. He created this GitHub
  repository and coordinated work across all four team members.
  
  ## Mustafa Rehman — Embedded System Developer
  
  Mustafa handled all physical hardware and GPIO programming.
  He wired all three HC-SR04 ultrasonic sensors to the Raspberry
  Pi 5 using the direct wire method without a breadboard. For each
  sensor he built a voltage divider using 1K and 2.2K resistors to
  reduce the 5V ECHO signal to 3.4V safe for the Pi GPIO pins.
  He mounted the sensors on a curved head with the left sensor
  angled 15 degrees left, center facing straight, and right sensor
  angled 15 degrees right giving 45 degrees total coverage.
  He calibrated the speed of sound to 34900 cm/s for Pakistan
  temperature instead of the standard European 34300 value.
  He implemented a 7-reading median filter for stable distances.
  He wired the push button on GPIO3 and set up the system auto
  boot service so the project starts automatically on Pi power-on.
  
  ## Noor Fatima — Software and Voice System Developer
  
  Noor built the entire voice and Bluetooth system. She integrated
  speak text-to-speech engine for offline voice output and created
  two functions: say() which blocks and waits for announcements to
  complete, and speak() which runs in a background thread so the
  detection pipeline never pauses. She added a threading Lock to
  prevent voice overlap. She wrote the Bluetooth auto-connect logic
  that tries the saved device MAC first on startup and falls back to
  scanning if needed. She added a watchdog thread that reconnects
  every 15 seconds if the audio device disconnects, and a keepalive
  thread that maintains 100 percent volume every 10 seconds.
  She wrote the cm to speech function converting raw centimeter values
  to natural phrases and the button state machine for sleep, wake,
  and shutdown controls.
  
  ## Safia 
