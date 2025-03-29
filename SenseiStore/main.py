from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import json

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '192.168.238.123'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_TOPICS'] = ['camera/detection', 'camera/videostreaming']

mqtt = Mqtt(app)
socketio = SocketIO(app)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        topic = message.topic

        if topic == 'camera/detection':
            socketio.emit('mqtt_message', payload)

        elif topic == 'camera/videostreaming':
            # Send the image to frontend (as base64)
            socketio.emit('stream_frame', payload)

    except Exception as e:
        print("❌ Failed to process MQTT message:", e)

# ========== FRONTEND ==========
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    for topic in app.config['MQTT_TOPICS']:
        mqtt.subscribe(topic)
    socketio.run(app, host='0.0.0.0', port=5000)
