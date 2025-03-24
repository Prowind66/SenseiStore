from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import json

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '192.168.238.123'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_TOPIC'] = 'camera/detection'

mqtt = Mqtt(app)
socketio = SocketIO(app)

# ========== MQTT MESSAGE RECEIVED ==========
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        # print("🔄 MQTT message:", payload)
        socketio.emit('mqtt_message', payload)  # Push to frontend in real-time
    except Exception as e:
        print("❌ Failed to process MQTT message:", e)

# ========== FRONTEND ==========
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    mqtt.subscribe(app.config['MQTT_TOPIC'])
    socketio.run(app, host='0.0.0.0', port=5000)
