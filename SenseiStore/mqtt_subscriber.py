# mqtt_subscriber.py
import paho.mqtt.client as mqtt
import base64
import json
import cv2
import numpy as np

latest_data = {
    "timestamp": "N/A",
    "emotion": "N/A",
    "bounding_box": [],
    "image_path": "static/images/face.jpg"
}

def decode_and_save_image(image_b64, path="static/images/face.jpg"):
    image_bytes = base64.b64decode(image_b64)
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    cv2.imwrite(path, image)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"📥 Received payload with emotion: {payload['emotion']}")

        decode_and_save_image(payload["image_b64"])
        latest_data["timestamp"] = payload["timestamp"]
        latest_data["emotion"] = payload["emotion"]
        latest_data["bounding_box"] = payload["bounding_box"]
        
    except Exception as e:
        print("⚠️ Error decoding message:", e)

def run_mqtt_subscriber():
    client = mqtt.Client()
    client.on_message = on_message

    client.connect("192.168.238.123", 1883)
    client.subscribe("camera/detection")
    client.loop_start()

    return latest_data
