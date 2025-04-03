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
        self.sensor = DistanceSensor(echo=echo_pin, trigger=trig_pin, max_distance=2)
        self.threshold_distance = 80

    def measure_distance(self):
        dist_cm = self.sensor.distance * 100
        return round(dist_cm, 2)

class MultiDetector:
    def __init__(self):
        self.face_model = YOLO("model/yolov11n-face.pt")
        self.drink_model = YOLO("my_model.pt")
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="Publisher")
        self.client.connect("192.168.238.123", 1883)
        self.client.loop_start()
        self.mqtt_topic = ["camera/detection", "camera/videostreaming", "camera/softdrink"]
        self.frame_queue = queue.Queue(maxsize=1)
        self.running_flag = [True]
        self.cap = None
        self.min_confidence = 0.8
        self.previous_face = None
        self.previous_emotion = None
        self.frame_counter = 0
        self.frame_skip = 3
        # self.detection_interval = 10
        self.custom_names = {
                0: {"name": "Osulloc Samdayeon Honey Pear Tea", "id": "160"},
                1: {"name": "Monster Energy Can Drink - Mango Loco", "id": "147"},
                2: {"name": "Pokka Bottle Drink - Jasmine Green Tea", "id": "3"},
                3: {"name": "Schwepps Tonic", "id": "159"}
            }

    def camera_capture_thread(self, cap):
        while self.running_flag[0]:
            ret, frame = cap.read()
            if ret and not self.frame_queue.full():
                self.frame_queue.put(frame)
            time.sleep(0.03)

    def processing_thread(self):
        while True:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()  
                self.frame_counter += 1
                # 1. Publish live video stream
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
                    print("❌ Failed to publish image stream:", e)

                # if self.frame_counter % self.frame_skip != 0:
                #     continue
                # 2. Face detection & emotion
                
                results = self.face_model(frame, imgsz=256)
                # face_found = False

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
                        # crop_height, crop_width = face_crop.shape[:2]
                        # print(f"🖼️ Face Crop Size: width = {crop_width}, height = {crop_height}")       

                        try:
                            # start_time = time.time()
                            emotion_analysis = DeepFace.analyze(
                                face_crop,
                                actions=['emotion'],
                                detector_backend='skip',
                                enforce_detection=True,
                            )
                            # end_time = time.time()
                            # deepface_duration = round((end_time - start_time) * 1000, 2)
                            # print(f"🧠 DeepFace analysis took {deepface_duration} ms")

                            emotion = emotion_analysis[0]['dominant_emotion']
                            success, encoded_face = cv2.imencode('.jpg', face_crop)
                            if not success:
                                continue
                            face_b64 = base64.b64encode(encoded_face).decode('utf-8')
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                            payload = {
                                "timestamp": timestamp,
                                "emotion": emotion,
                                "image_b64": face_b64,
                                "confidence_score": conf
                            }
                            self.client.publish(self.mqtt_topic[0], json.dumps(payload))
                            # print(f"📤 Emotion published: {list(payload.keys())}")
                            # face_found = True

                        except Exception as e:
                            print("⚠️ DeepFace Error:", e)

                # 3. Softdrink detection (only if face was detected)
                # if face_found:
                # if softdrink_counter < self.detection_interval:
                    # continue  # skip softdrink detection this round
                # softdrink_counter = 0  # reset after triggering

                try:
                    drink_results = self.drink_model(frame,imgsz=256)

                    for result in drink_results:
                        for box in result.boxes:

                            conf = round(box.conf[0].item(), 2)
                            if conf < 0.8:
                                continue
                            cls_id = int(box.cls[0])
                            class_info = self.custom_names.get(cls_id, {"name": f"Unknown-{cls_id}", "id": str(cls_id)})
                            product_name = class_info["name"]
                            product_id = class_info["id"]

                            # print("class_name",class_name)
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            drink_crop = frame[int(y1):int(y2), int(x1):int(x2)]
                            success, encoded_drink = cv2.imencode('.jpg', drink_crop)
                            if not success:
                                continue
                            drink_b64 = base64.b64encode(encoded_drink).decode('utf-8')

                            payload = {
                                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                                "product_id": product_id,
                                "product_name": product_name,
                                "confidence_score": conf,
                                "image_b64": drink_b64
                            }
                            self.client.publish(self.mqtt_topic[2], json.dumps(payload))
                            print(f"🥤 Softdrink published: {product_name} ({conf})")
                except Exception as e:
                    print("⚠️ Softdrink Error:", e)

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
                        self.cap.set(cv2.CAP_PROP_FPS, 30)
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  
                        threading.Thread(target=self.camera_capture_thread, args=(self.cap,), daemon=True).start()
                else:
                    if self.cap is not None:
                        print("No person. Releasing camera...")
                        self.running_flag[0] = False
                        self.cap.release()
                        self.cap = None
                        self.running_flag[0] = True
                time.sleep(0.2)

        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            self.running_flag[0] = False
            if self.cap is not None:
                self.cap.release()
            self.client.loop_stop()
            self.client.disconnect()
            print("Exiting gracefully...")

if __name__ == '__main__':
    sensor = UltrasonicSensor(23, 24)
    detector = MultiDetector()
    detector.run(sensor, threshold_distance=80.0)
