import cv2
import os
import json
from datetime import datetime
from ultralytics import YOLO
from deepface import DeepFace
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# MQTT Configuration
MQTT_BROKER = "192.168.40.75"  # Replace with your Laptop's IP
MQTT_PORT = 1883
MQTT_TOPIC = "camera/detection"

# Initialize MQTT Client
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="Publisher")
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

# Create an "images" folder if it doesn't exist
os.makedirs("images", exist_ok=True)

# Load YOLO model for face detection
face_model = YOLO("yolov11n-face.pt")

# Initialize webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Error: Unable to capture frame.")
        break

    # Run YOLO face detection
    results = face_model(frame)
    detected_faces = []  # List to store face bounding box coordinates
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Extract face bounding box
            detected_faces.append((x1, y1, x2, y2))  # Store detected face
            # Crop detected face
            face_crop = frame[y1:y2, x1:x2]

            # Ensure the face is large enough before processing
            if face_crop.shape[0] > 30 and face_crop.shape[1] > 30:
                try:
                    # Detect emotion using DeepFace
                    emotion_analysis = DeepFace.analyze(face_crop, actions=['emotion'], detector_backend='opencv', enforce_detection=False)
                    emotion = emotion_analysis[0]['dominant_emotion']

                    # ✅ Draw bounding boxes and emotion label
                    for (x1, y1, x2, y2) in detected_faces:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green Box
                        cv2.putText(frame, emotion, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    # Generate a unique filename using timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_filename = f"images/face_{timestamp}.jpg"

                    # Save the cropped face image
                    cv2.imwrite(image_filename, frame)

                    # Open and send raw image binary
                    with open(image_filename, "rb") as img_file:
                        image_binary = img_file.read()

                    # Publish metadata JSON
                    metadata = {
                        "timestamp": timestamp,
                        "emotion": emotion
                    }
                    client.publish(MQTT_TOPIC + "/metadata", json.dumps(metadata))
                    print(f"📤 Sent Metadata: {metadata}")

                    # Publish raw image separately
                    client.publish(MQTT_TOPIC + "/image", image_binary)
                    print("📤 Sent MQTT raw image data.")

                except Exception as e:
                    print("⚠️ DeepFace Error:", e)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()