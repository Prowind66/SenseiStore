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

import base64  # For base64 encoding the image

# ============================= GPIO SETUP ============================= #
TRIG = 23  # GPIO 23 (Pin 16)
ECHO = 24  # GPIO 24 (Pin 18)

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def measure_distance():
    """
    Return distance in centimeters, or None on timeout.
    """
    # Let the sensor settle
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    # Trigger sensor
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)

    # Wait for ECHO to go HIGH
    timeout_start = time.time()
    pulse_start = None
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if (time.time() - timeout_start) > 0.02:  # ~ 20ms
            return None  # Timeout => return None

    # Wait for ECHO to go LOW
    timeout_start = time.time()
    pulse_end = None
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if (time.time() - timeout_start) > 0.02:  # ~ 20ms
            return None  # Timeout => return None

    if pulse_start is None or pulse_end is None:
        return None  # Safety check

    # Calculate distance in cm (speed of sound ~34300 cm/s)
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2
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
        if dist is None:
            # Sensor timed out or gave invalid reading
            print("Ultrasonic Error: Timeout/Invalid reading.")
            time.sleep(1)  # Wait a bit and then try again
            continue

        print(f"Distance: {dist} cm")

        if dist < THRESHOLD_DISTANCE:
            # Something is close; ensure camera is ON
            if cap is None:
                print("Person detected. Opening camera...")
                cap = cv2.VideoCapture(0)

            ret, frame = cap.read()
            if not ret:
                print("⚠️ Error: Could not read from camera.")
            else:
                # ==================== YOLO Face Detection ==================== #
                results = face_model(frame)
                for result in results:
                    for box in result.boxes:
                        h, w, _ = frame.shape
                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                        # Dynamic margin based on face size
                        face_width = x2 - x1
                        face_height = y2 - y1
                        margin = max(int(min(face_width, face_height) * 0.5), 30)

                        # Margin clipping
                        x1m = max(x1 - margin, 0)
                        y1m = max(y1 - margin, 0)
                        x2m = min(x2 + margin, w)
                        y2m = min(y2 + margin, h)

                        face_crop = frame[y1m:y2m, x1m:x2m]

                        # Only process if large enough
                        if face_crop.shape[0] > 60 and face_crop.shape[1] > 60:
                            try:
                                emotion_analysis = DeepFace.analyze(
                                    face_crop,
                                    actions=['emotion'],
                                    detector_backend='skip',
                                    enforce_detection=False,
                                )
                                emotion = emotion_analysis[0]['dominant_emotion']

                                success, encoded_face = cv2.imencode('.jpg', frame)
                                if not success:
                                    print("⚠️ Could not encode face_crop.")
                                    continue

                                face_b64 = base64.b64encode(encoded_face).decode('utf-8')
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                                payload = {
                                    "timestamp": timestamp,
                                    "bounding_box": [x1, y1, x2, y2],
                                    "emotion": emotion,
                                    "image_b64": face_b64
                                }

                                client.publish(MQTT_TOPIC, json.dumps(payload))
                                print(f"📤 Published: {list(payload.keys())}")

                            except Exception as e:
                                print("⚠️ DeepFace Error:", e)

        else:
            # Nothing close; ensure camera is OFF
            if cap is not None:
                print("No person. Releasing camera...")
                cap.release()
                cap = None

        time.sleep(1)  # Check distance again after 1 second

except KeyboardInterrupt:
    print("Interrupted by user.")
finally:
    # Cleanup on exit
    if cap is not None:
        cap.release()
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()
    print("Exiting gracefully...")
