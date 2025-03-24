import RPi.GPIO as GPIO
import time
import cv2
import json
import base64
import threading
import queue
from datetime import datetime
from ultralytics import YOLO
from deepface import DeepFace
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

class UltrasonicSensor:
    def __init__(self, trig_pin, echo_pin):
        self.trig = trig_pin
        self.echo = echo_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def measure_distance(self):
        GPIO.output(self.trig, False)
        time.sleep(0.05)
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        timeout_start = time.time()
        pulse_start = None
        while GPIO.input(self.echo) == 0:
            pulse_start = time.time()
            if (time.time() - timeout_start) > 0.02:
                return None

        timeout_start = time.time()
        pulse_end = None
        while GPIO.input(self.echo) == 1:
            pulse_end = time.time()
            if (time.time() - timeout_start) > 0.02:
                return None

        if pulse_start is None or pulse_end is None:
            return None

        pulse_duration = pulse_end - pulse_start
        distance = (pulse_duration * 34300) / 2
        return round(distance, 2)

class EmotionDetector:
    def __init__(self):
        self.face_model = YOLO("yolov11n-face.pt")
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="Publisher")
        self.client.connect("192.168.238.123", 1883)
        self.client.loop_start()
        self.mqtt_topic = "camera/detection"
        self.frame_queue = queue.Queue(maxsize=1)
        self.running_flag = [True]
        self.cap = None

    def camera_capture_thread(self,cap):
        while self.running_flag[0]:
            ret, frame = cap.read()
            if ret and not self.frame_queue.full():
                self.frame_queue.put(frame)
            time.sleep(0.05)

    def processing_thread(self):
        while True:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                results = self.face_model(frame, imgsz=256)
                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        margin = 30
                        h, w, _ = frame.shape
                        x1m = max(x1 - margin, 0)
                        y1m = max(y1 - margin, 0)
                        x2m = min(x2 + margin, w)
                        y2m = min(y2 + margin, h)
                        face_crop = frame[y1m:y2m, x1m:x2m]

                        try:
                            emotion_analysis = DeepFace.analyze(
                                face_crop,
                                actions=['emotion'],
                                detector_backend='skip',
                                enforce_detection=True,
                            )
                            emotion = emotion_analysis[0]['dominant_emotion']
                            success, encoded_face = cv2.imencode('.jpg', face_crop)
                            if not success:
                                continue
                            face_b64 = base64.b64encode(encoded_face).decode('utf-8')
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            payload = {
                                "timestamp": timestamp,
                                "bounding_box": [x1, y1, x2, y2],
                                "emotion": emotion,
                                "image_b64": face_b64
                            }
                            self.client.publish(self.mqtt_topic, json.dumps(payload))
                            print(f"📤 Published: {list(payload.keys())}")

                        except Exception as e:
                            print("⚠️ DeepFace Error:", e)

    def run(self, sensor, threshold_distance):
        try:
            threading.Thread(target=self.processing_thread, daemon=True).start()
            while True:
                dist = sensor.measure_distance()
                print(f"Distance: {dist} cm")

                if dist is not None and dist < threshold_distance:
                    if self.cap is None:
                        print("Person detected. Opening camera...")
                        self.cap = cv2.VideoCapture(0)
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        threading.Thread(target=self.camera_capture_thread, args=(self.cap,), daemon=True).start()
                else:
                    if self.cap is not None:
                        print("No person. Releasing camera...")
                        self.running_flag[0] = False
                        self.cap.release()
                        self.cap = None
                        self.running_flag[0] = True

                time.sleep(1)

        except KeyboardInterrupt:
            print("Interrupted by user.")

        finally:
            self.running_flag[0] = False
            if self.cap is not None:
                self.cap.release()
            GPIO.cleanup()
            self.client.loop_stop()
            self.client.disconnect()
            print("Exiting gracefully...")

if __name__ == '__main__':
    sensor = UltrasonicSensor(23, 24)
    detector = EmotionDetector()
    detector.run(sensor, threshold_distance=80.0)
