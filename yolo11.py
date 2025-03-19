import cv2
import torch
import os
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from deepface import DeepFace

# Create an "images" folder if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")

# Load YOLO model (ensure this model exists)
face_model = YOLO("yolov11n-face.pt")  # Use "yolov8n-face.pt" instead of "yolov11n-face.pt" (YOLO 11 does not exist)

# Initialize webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO face detection
    results = face_model(frame)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Extract face bounding box

            # Crop detected face
            face_crop = frame[y1:y2, x1:x2]

            # Ensure the face is large enough before emotion detection
            if face_crop.shape[0] > 30 and face_crop.shape[1] > 30:
                try:
                    # Detect emotion using DeepFace
                    emotion_analysis = DeepFace.analyze(face_crop, actions=['emotion'], detector_backend='opencv', enforce_detection=False)
                    emotion = emotion_analysis[0]['dominant_emotion']

                    # Draw bounding box around face
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{emotion}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Generate a unique filename using timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_filename = f"images/face_{timestamp}.jpg"

                    # Save the cropped face image
                    cv2.imwrite(image_filename, face_crop)
                    print(f"Saved face image: {image_filename}")

                except Exception as e:
                    print("DeepFace Error:", e)

    # Display the frame (optional, can be removed in embedded systems)
    cv2.imshow("Face & Emotion Detection", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
