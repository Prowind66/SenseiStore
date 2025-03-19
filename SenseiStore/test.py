import cv2
import base64
import json
import numpy as np
import paho.mqtt.client as mqtt

# MQTT Configuration (Desktop is Broker)
MQTT_BROKER = "localhost"  # Use "localhost" since this is running on the Desktop
MQTT_PORT = 1883
MQTT_TOPIC = "camera/image"

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT Broker (Desktop)")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print("📥 Image received!")
    payload = json.loads(msg.payload.decode())

    # Decode Base64 Image
    image_data = base64.b64decode(payload["image"])
    image_np = np.frombuffer(image_data, dtype=np.uint8)
    frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # Display Image
    cv2.imshow("MQTT Camera Feed", frame)
    cv2.waitKey(1)  # Refreshes the image frame

# Initialize MQTT Client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

client.loop_forever()  # Keep listening for messages
