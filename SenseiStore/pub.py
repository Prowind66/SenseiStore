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
from gpiozero import DistanceSensor

class UltrasonicSensor:
    def __init__(self, trig_pin, echo_pin):
        self.sensor = DistanceSensor(echo=echo_pin, trigger=trig_pin,max_distance=2)
    
    def measure_distance(self):
        dist_cm = self.sensor.distance * 100  # Convert to cm
        return round(dist_cm, 2)

class EmotionDetector:
    def __init__(self):
        self.face_model = YOLO("yolov11n-face.pt")
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="Publisher")
        self.client.connect("192.168.238.123", 1883)
        self.client.loop_start()
        self.mqtt_topic = ["camera/detection","camera/videostreaming"]
        self.frame_queue = queue.Queue(maxsize=1)
        self.running_flag = [True]
        self.cap = None
        self.min_confidence = 0.8

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
                # Publish current frame as image to camera/videostreaming
                try:
                    success, encoded_image = cv2.imencode('.jpg', frame)
                    if success:
                        image_b64 = base64.b64encode(encoded_image).decode('utf-8')
                        image_payload = {
                            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                            "image_b64": image_b64
                        }
                    self.client.publish(self.mqtt_topic[1], json.dumps(image_payload))
                except Exception as e:
                    print("❌ Failed to publish image to MQTT:", e)

                for result in results:
                    for box in result.boxes:
                        conf = round(box.conf[0].item(), 2)
                        if conf < self.min_confidence:
                            continue
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
                                "image_b64": face_b64,
                                "confidence_score" : conf
                            }
                            self.client.publish(self.mqtt_topic[0], json.dumps(payload))
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
                time.sleep(0.4)
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
