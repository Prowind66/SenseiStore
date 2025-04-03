from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import json
import pandas as pd
import random
import time
import os 
import playsound
import threading
from gtts import gTTS
from datetime import datetime

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '192.168.238.123'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_TOPICS'] = ['camera/detection', 'camera/videostreaming', 'camera/softdrink']

mqtt = Mqtt(app)
socketio = SocketIO(app)

cooldown = {"last_emotion": None, "last_time": 0, "cooldown_period": 7}
brand_cooldown = {"last_brand": None, "last_time": 0, "cooldown_period": 7}
tts_cooldown = {"last_tts_time": 0, "cooldown_period": 7}

def should_speak():
    now = time.time()
    if (now - tts_cooldown["last_tts_time"]) > tts_cooldown["cooldown_period"]:
        tts_cooldown["last_tts_time"] = now
        return True
    return False

def should_recommend_brand(current_brand):
    now = time.time()
    if current_brand != brand_cooldown["last_brand"] or (now - brand_cooldown["last_time"] > brand_cooldown["cooldown_period"]):
        print(f"✅ New Brand Detected: {current_brand}")
        brand_cooldown["last_brand"] = current_brand
        brand_cooldown["last_time"] = now
        return True
    else:
        print(f"⏭️ Skipping Brand: {current_brand} (Same or cooldown)")
    return False

def should_update_recommendation(current_emotion):
    now = time.time()
    if current_emotion != cooldown["last_emotion"] and (now - cooldown["last_time"] > cooldown["cooldown_period"]):
        print(f"✅ New Emotion Detected: {current_emotion}")
        cooldown["last_emotion"] = current_emotion
        cooldown["last_time"] = now
        return True
    else:
        print(f"⏭️ Skipping Emotion: {current_emotion} (Same or cooldown)")
    return False

def get_brand_recommendations(product_id):
    product_row = product_df[product_df['product_id'].astype(str) == str(product_id)]
    if product_row.empty:
        return []

    brand = product_row['product_company'].values[0]
    similar_products = sales_df[
        (sales_df['Product_Company'] == brand) &
        (product_df['product_id'].astype(str) != str(product_id))
    ].drop_duplicates('Product')

    recommendations = similar_products.sample(n=min(6, len(similar_products)))
    return recommendations[['Product', 'Product_Image_Url', 'Unit_Price']].to_dict(orient='records')

def get_recommendation_by_emotion(emotion):
    subset = sales_df.sample(6)
    return subset[['Product', 'Product_Image_Url', 'Unit_Price']].to_dict(orient='records')

def speak_recommendation(emotion, first_item):
    recommendations = {
        "happy": f"You seem happy! We recommend trying our {first_item} ",
        "sad": f"You seem a little down — maybe a refreshing {first_item} can lift your mood.",
        "angry": f"Feeling frustrated? A cold {first_item} might help cool things down.",
        "surprise": f"Looks like that caught your attention! {first_item} is full of surprises",
        "disgust": f"Not your vibe? No worries — we’ve got 9 other drinks that might be a better match than {first_item}.",
        "fear": f"Not sure about that one? {first_item} is a safe choice",
        "neutral": f"Hard to tell what you think — maybe {first_item} will change your mind?"
    }
    message = recommendations.get(emotion, "Try one of our top drinks today!")
    try:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_rec.mp3"
        tts = gTTS(text=message, lang='en')
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)
    except Exception as e:
        print("🔊 TTS Error:", e)

def speak_brand_recommendation(brand_name):
    try:
        message = f"You seem to be interested in {brand_name}. How about these few?"
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_brand.mp3"
        tts = gTTS(text=message, lang='en')
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)
    except Exception as e:
        print("🔊 TTS Error:", e)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        topic = message.topic

        if topic == 'camera/detection':
            if should_update_recommendation(payload['emotion']):
                recommended_items = get_recommendation_by_emotion(payload['emotion'])
                socketio.emit('emotion_recommendation', {
                    "emotion": payload['emotion'],
                    "recommendations": recommended_items
                })
                if recommended_items and should_speak():
                    first_item = recommended_items[0]['Product']
                    threading.Thread(target=speak_recommendation, args=(payload['emotion'], first_item), daemon=True).start()
            socketio.emit('mqtt_message', payload)

        elif topic == 'camera/videostreaming':
            socketio.emit('stream_frame', payload)

        if topic == 'camera/softdrink':
            socketio.emit('softdrink', payload)
            product_id = payload['product_id']
            product_row = product_df[product_df['product_id'].astype(str) == str(product_id)]
            if not product_row.empty:
                brand = product_row['product_company'].values[0]
                if should_recommend_brand(brand) and should_speak():
                    brand_recommendations = get_brand_recommendations(product_id)
                    socketio.emit('product_recommendation', {
                        "product_id": product_id,
                        "brand": brand,
                        "recommendations": brand_recommendations
                    })
                    threading.Thread(target=speak_brand_recommendation, args=(brand,), daemon=True).start()

    except Exception as e:
        print("❌ Failed to process MQTT message:", e)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    sales_df = pd.read_csv("scraping/synthetic_sales_data.csv", encoding="utf-8")
    product_df = pd.read_csv("scraping/drinks_content_edited.csv", encoding="utf-8")
    for topic in app.config['MQTT_TOPICS']:
        mqtt.subscribe(topic)
    socketio.run(app, host='0.0.0.0', port=5000)
