import paho.mqtt.client as mqtt
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# MQTT Config
MQTT_BROKER = "127.0.0.1"
MQTT_USER = "mqtt"
MQTT_PW = "mqtt"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toggle/<int:relay_id>/<state>')
def toggle(relay_id, state):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PW)
    client.connect(MQTT_BROKER, 1883)
    # This matches the topic in your PicoW script
    topic = f"jumilla/picow_cotroller_hat_1/switch{relay_id}/set"
    client.publish(topic, state)
    client.disconnect()
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
