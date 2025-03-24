import paho.mqtt.client as mqtt
import json
import os
import cv2
import numpy as np
import base64

# MQTT Configuration
MQTT_BROKER = "192.168.238.123"
MQTT_PORT = 1883
MQTT_TOPIC = "camera/detection"  # Single topic publishing both metadata + base64 image

# Create directories if not exist
os.makedirs("received_images", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        # Subscribe to the single topic that carries the combined JSON
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        # 1) Parse the incoming JSON
        data = json.loads(msg.payload.decode())
        print(f"\n📥 Received keys: {list(data.keys())}")

        # 2) Extract metadata (timestamp, emotion, bounding_box, etc.)
        timestamp = data.get("timestamp", "Unknown")
        emotion = data.get("emotion", "Unknown")

        # 3) Retrieve the Base64-encoded image string
        image_b64 = data.get("image_b64")
        if not image_b64:
            print("⚠️ No 'image_b64' found in the JSON payload. Skipping image processing.")
            return

        # 4) Decode Base64 → bytes → NumPy array → OpenCV image
        image_bytes = base64.b64decode(image_b64)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if img is not None:
            # 5) Save the received image locally
            image_filename = f"received_images/face_{timestamp}.jpg"
            cv2.imwrite(image_filename, img)
            print(f"💾 Image saved as: {image_filename}")

            # 6) Display the image in a window for 1 second
            cv2.imshow(f"Emotion: {emotion}", img)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
        else:
            print("⚠️ Error: Could not decode the received image.")

    except json.JSONDecodeError:
        print(f"⚠️ Error: Invalid JSON format in message: {msg.payload.decode()}")
    except Exception as e:
        print(f"⚠️ Unexpected error in on_message: {e}")

# Initialize MQTT Client
client = mqtt.Client(client_id="Subscriber")
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    print("📡 Waiting for messages...")
    client.loop_forever()
except Exception as e:
    print(f"❌ MQTT Connection Error: {e}")
