import RPi.GPIO as GPIO
import time
import cv2
import os
import json
from datetime import datetime
from ultralytics import YOLO
from deepface import DeepFace
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

import base64  # <-- We need this for base64 encoding the image

# ============================= GPIO SETUP ============================= #
TRIG = 23  # GPIO 23 (Pin 16)
ECHO = 24  # GPIO 24 (Pin 18)

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def measure_distance():
    """Return distance in centimeters or an error string on timeout."""
    # Reset Echo pin
    GPIO.setup(ECHO, GPIO.OUT)
    GPIO.output(ECHO, False)
    time.sleep(0.1)
    GPIO.setup(ECHO, GPIO.IN)

    # Trigger sensor
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)

    timeout_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if (time.time() - timeout_start) > 0.02:
            return "Timeout waiting for Echo HIGH"

    timeout_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if (time.time() - timeout_start) > 0.02:
            return "Timeout waiting for Echo LOW"

    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2  # Speed of sound = 34300 cm/s
    return round(distance, 2)

# ============================= MQTT SETUP ============================= #
MQTT_BROKER = "192.168.238.123"
MQTT_PORT = 1883
MQTT_TOPIC = "camera/detection"

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="Publisher")
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

# ============================= YOLO SETUP ============================= #
face_model = YOLO("yolov11n-face.pt")  # Replace with your face-specific YOLO model

# ============================= MAIN LOOP ============================= #
THRESHOLD_DISTANCE = 60.0  # cm
cap = None  # We'll open/close this dynamically

try:
    while True:
        dist = measure_distance()

        if isinstance(dist, str):
            print(f"Ultrasonic Error: {dist}")
            time.sleep(1)
            continue

        print(f"Distance: {dist} cm")

        if dist < THRESHOLD_DISTANCE:
            # Person is close; ensure camera is ON
            if cap is None:
                print("Person detected. Opening camera...")
                cap = cv2.VideoCapture(0)

            ret, frame = cap.read()
            if not ret:
                print("⚠️ Error: Could not read from camera.")
            else:
                # 1) YOLO Face Detection
                results = face_model(frame)
                for result in results:
                    for box in result.boxes:
                        h, w, _ = frame.shape
                        margin = 30
                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                         # Apply 30-pixel margin with bounds checking
                        x1m = max(x1 - margin, 0)
                        y1m = max(y1 - margin, 0)
                        x2m = min(x2 + margin, w)
                        y2m = min(y2 + margin, h)

                        face_crop = frame[y1m:y2m, x1m:x2m]

                        if face_crop.shape[0] > 30 and face_crop.shape[1] > 30:
                            try:
                                # 2) DeepFace Emotion
                                emotion_analysis = DeepFace.analyze(
                                    face_crop,
                                    actions=['emotion'],
                                    detector_backend='opencv',
                                    enforce_detection=False
                                )
                                emotion = emotion_analysis[0]['dominant_emotion']

                                # 3) Encode the face_crop as JPEG
                                success, encoded_face = cv2.imencode('.jpg', face_crop)
                                if not success:
                                    print("⚠️ Could not encode face_crop.")
                                    continue

                                # 4) Base64-encode to embed in JSON
                                face_b64 = base64.b64encode(encoded_face).decode('utf-8')

                                # 5) Prepare a single JSON payload
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                payload = {
                                    "timestamp": timestamp,
                                    "bounding_box": [x1, y1, x2, y2],
                                    "emotion": emotion,
                                    "image_b64": face_b64
                                }

                                # 6) Publish the JSON payload
                                client.publish(MQTT_TOPIC, json.dumps(payload))
                                print(f"📤 Published: {list(payload.keys())}")

                            except Exception as e:
                                print("⚠️ DeepFace Error:", e)
        else:
            # Person is NOT close; ensure camera is OFF
            if cap is not None:
                print("No person. Releasing camera...")
                cap.release()
                cap = None

        time.sleep(1)  # Check distance again after 1 second

except KeyboardInterrupt:
    print("Interrupted by user.")
finally:
    if cap is not None:
        cap.release()
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()
    print("Exiting gracefully...")
