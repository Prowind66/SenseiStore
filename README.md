# SenseiStore
SenseiStore is an AI-powered Interactive Retail Solution that can help enhance customer user experience by detecting emotions using a proximity sensor and camera, then provides product recommendations through a UI and speaker system

## Key Features
1. Proximity Detection: Ultrasonic sensor detects customer presence
2. Emotion Recognition: Camera analyzes facial expressions
3. Product Recommendations: AI suggests products via screen and speaker

## Prerequisite Software And Technologies Used
1. Python
2. MQTT 
3. Install Packages From requirements.txt

## Models Experimented
| Model             | Purpose         | Total Inference Time Per Frame|
|-------------------|-----------------|-------------|
| RetinaFace        | Face Detection  | ~200ms - ~300ms 
| yolov11m-face     | Face Detection  | ~1200ms - ~1300ms
| yolov11n-face     | Face Detection  | ~180ms - ~220ms |
| deepface          | Emotion Detection  | ~40ms - ~47ms |

## Hardware Used
1. Raspberry Pi 400 x2 (x1 Broker, x1 Publisher)
2. Logitech C310 HD WebCam (HD 720p/30fps)
3. Laptop Or Desktop (x1 Subscriber/Frontend)
4. Ultrasonic Sensor (HC-SR04)
