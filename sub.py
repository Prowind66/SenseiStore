import paho.mqtt.client as mqtt
import json
import os
import cv2
import numpy as np

# MQTT Configuration
MQTT_BROKER = "192.168.40.75"
MQTT_PORT = 1883
MQTT_TOPIC_METADATA = "camera/detection/metadata"
MQTT_TOPIC_IMAGE = "camera/detection/image"

# Create directories if not exist
os.makedirs("received_images", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Global variable to store latest metadata
latest_metadata = {}

# Callback function when connected
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe([(MQTT_TOPIC_METADATA, 0), (MQTT_TOPIC_IMAGE, 0)])
    else:
        print(f"❌ Connection failed with code {rc}")

# Callback function for metadata (JSON)
def on_metadata_message(client, userdata, msg):
    global latest_metadata
    try:
        # Decode JSON metadata
        latest_metadata = json.loads(msg.payload.decode())
        print(f"\n📥 Received Metadata: {latest_metadata}")

    except json.JSONDecodeError:
        print(f"⚠️ Error: Received invalid JSON metadata: {msg.payload.decode()}")

# Callback function for image (binary data)
def on_image_message(client, userdata, msg):
    if not latest_metadata:
        print("⚠️ No metadata received yet. Skipping image processing.")
        return

    timestamp = latest_metadata.get("timestamp", "Unknown")
    emotion = latest_metadata.get("emotion", "Unknown")

    # Convert raw binary image data into OpenCV format
    image_array = np.frombuffer(msg.payload, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if img is not None:
        # Save received image
        image_filename = f"received_images/face_{timestamp}.jpg"
        cv2.imwrite(image_filename, img)
        print(f"💾 Image saved as: {image_filename}")

        # Display the image
        cv2.imshow(f"Emotion: {emotion}", img)
        cv2.waitKey(1000)  # Display for 1 second
        cv2.destroyAllWindows()
    else:
        print("⚠️ Error: Could not decode the received image.")

# Initialize MQTT Client
client = mqtt.Client(client_id="Subscriber")
client.on_connect = on_connect
client.message_callback_add(MQTT_TOPIC_METADATA, on_metadata_message)
client.message_callback_add(MQTT_TOPIC_IMAGE, on_image_message)

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    print("📡 Waiting for messages...")
    client.loop_forever()
except Exception as e:
    print(f"❌ MQTT Connection Error: {e}")
