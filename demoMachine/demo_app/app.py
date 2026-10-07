"""
app.py — demoMachine dashboard for the coop controller demo.

This is an HMI, not a controller. The Pico owns the relays, the door input and
the probe, so it is the only thing that can tell the truth about them; this app
subscribes, caches what it hears, and renders it. It never invents state.

HOW THE DATA GETS HERE — only the last hop is polled:

    Pico  --push-->  Mosquitto  --push-->  this app's cache  --500ms poll-->  browser

The MQTT half is push: paho runs a background thread that hands us every message
the instant it is published, so a relay toggle or a door edge lands in the cache
with no request from anyone. The browser polls /api/state because plain HTTP has
no way to be pushed to; that is the hop you would replace with SSE later, and
nothing else about this file would change.

WHY A MODULE-LEVEL CLIENT IS SAFE HERE, AND WHEN IT WOULD NOT BE:

Everything below the "MQTT holder" heading runs ONCE, at import, per worker
process. The systemd unit starts gunicorn as

    gunicorn --threads 4 --bind 127.0.0.1:5000 app:app

which is ONE process with four threads, so there is exactly one MQTT connection
and one cache, and all four request threads read the same dict. Add --workers 2
and you get two processes, two connections, two independent caches, and a
dashboard that shows different answers depending on which worker served the
request. If you ever need more workers, the cache has to move out of the process
(Redis, a database) or the push has to move to SSE from a single publisher.

The cache is written by paho's thread and read by Flask's request threads, which
is why every touch of it takes _lock.
"""

import json
import threading
import time
from collections import deque

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
# The broker runs on this same Pi, so the dashboard reaches it over loopback.
# The Pico reaches the same broker across the hotspot at 192.168.4.1.

MQTT_BROKER = '127.0.0.1'
MQTT_PORT   = 1883
MQTT_USER   = 'mqtt'
MQTT_PW     = 'mqtt'

DEVICE = 'demo/coop_1'   # the device this dashboard is pointed at
WATCH  = 'demo/#'        # subscribe to everything, so the traffic pane shows
                         # commands and other devices too, not just our widgets

TRAFFIC_MAX = 300        # ring buffer depth for the traffic pane

# Topic suffix -> widget key. Anything not listed still appears in the traffic
# pane; it just doesn't drive a lamp.
WIDGET_TOPICS = {
    'status':        'status',
    'switch1/state': 'switch1',
    'switch2/state': 'switch2',
    'door':          'door',
    'temp_c':        'temp_c',
    'reset_cause':   'reset_cause',
}

VALID_ACTIONS  = ('on', 'off', 'toggle')
VALID_REQUESTS = ('ping', 'state', 'health', 'pins', 'reset')

# ─── MQTT holder ─────────────────────────────────────────────────────────────

_lock = threading.Lock()

_state = {
    'status':       None,   # 'online' / 'offline' — from the Pico's LWT
    'switch1':      None,
    'switch2':      None,
    'door':         None,
    'temp_c':       None,
    'reset_cause':  None,
    'wifi':         None,   # parsed JSON
    'health':       None,   # parsed JSON
    'last_seen':    None,   # unix time of the last message from DEVICE
}

_traffic = deque(maxlen=TRAFFIC_MAX)
_seq = 0                  # monotonic cursor, so the browser can ask "what's new"
_broker_connected = False


def _classify(topic):
    """Colour-coding for the traffic pane — what KIND of message this is."""
    if topic.endswith('/set') or topic.endswith('/request'):
        return 'cmd'
    if topic.endswith('/log'):
        return 'log'
    if topic.endswith('/health') or topic.endswith('/wifi') or topic.endswith('/pins'):
        return 'diag'
    if topic.endswith('/response'):
        return 'reply'
    return 'state'


def _record(topic, payload, retained):
    """Append one message to the ring buffer. Caller holds _lock."""
    global _seq
    _seq += 1
    _traffic.append({
        'seq':      _seq,
        't':        time.strftime('%H:%M:%S'),
        'topic':    topic,
        'payload':  payload,
        'retained': bool(retained),
        'kind':     _classify(topic),
    })


def _on_connect(client, userdata, flags, reason_code, properties=None):
    """Subscribing here, not at startup, is deliberate: on_connect fires again
    after every reconnect, and a subscription made before a drop does not
    survive it. The broker replays retained messages on subscribe, so the cache
    refills itself within milliseconds of reconnecting."""
    global _broker_connected
    with _lock:
        _broker_connected = (reason_code == 0)
    if reason_code == 0:
        client.subscribe(WATCH, qos=1)
        print(f"[mqtt] connected, subscribed to {WATCH}")
    else:
        print(f"[mqtt] connect failed: {reason_code}")


def _on_disconnect(client, userdata, flags, reason_code, properties=None):
    global _broker_connected
    with _lock:
        _broker_connected = False
    print(f"[mqtt] disconnected ({reason_code}) — paho will retry")


def _on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8', 'replace')
    with _lock:
        _record(msg.topic, payload, msg.retain)

        if not msg.topic.startswith(DEVICE + '/'):
            return
        suffix = msg.topic[len(DEVICE) + 1:]
        _state['last_seen'] = time.time()

        key = WIDGET_TOPICS.get(suffix)
        if key:
            # An empty payload on a retained topic is the firmware DELETING the
            # retained value — "I no longer know this" — so it becomes None and
            # the widget shows '--' rather than a stale number that looks live.
            _state[key] = payload if payload != '' else None
        elif suffix in ('wifi', 'health'):
            try:
                _state[suffix] = json.loads(payload)
            except ValueError:
                pass


_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='demo_dashboard')
_client.username_pw_set(MQTT_USER, MQTT_PW)
_client.on_connect = _on_connect
_client.on_disconnect = _on_disconnect
_client.on_message = _on_message

# connect_async, not connect: connect() raises if the broker isn't up yet, which
# would crash the app at import and leave systemd restart-looping. This way the
# dashboard starts regardless and shows "broker: down" until Mosquitto answers.
_client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
_client.loop_start()


def _publish(topic, payload):
    """Fire a command at the device.

    No local state is updated here on purpose. The command goes to the broker,
    the Pico acts on it and publishes the resulting state, and we learn the
    outcome the same way any other subscriber does. If the Pico is unplugged the
    lamp does NOT move — which is the correct and much more useful behaviour
    than a UI that pretends the command worked.

    The outgoing message also comes straight back to us, because we subscribe to
    demo/# — which is why commands appear in the traffic pane for free.
    """
    _client.publish(topic, payload, qos=1)
    print(f"[mqtt] -> {topic} {payload}")

# ─── Routes ──────────────────────────────────────────────────────────────────


@app.route('/')
def index():
    return render_template('index.html', device=DEVICE,
                           broker_hint=f'mosquitto_sub -h 192.168.4.1 -u mqtt -P mqtt -t \'demo/#\' -v')


@app.route('/api/state')
def api_state():
    """Everything the page needs, in one request.

    `since` is the cursor: pass back the `seq` from the previous reply and you
    get only the traffic that has arrived since, so the pane appends instead of
    redrawing and nothing is shown twice. First load sends since=0 and gets the
    whole buffered backlog, which is a nice thing to land on.
    """
    since = request.args.get('since', default=0, type=int)
    with _lock:
        messages = [m for m in _traffic if m['seq'] > since]
        return jsonify(
            state=dict(_state),
            messages=messages,
            seq=_seq,
            broker=_broker_connected,
            device=DEVICE,
        )


@app.route('/api/switch/<int:n>/<action>', methods=['GET', 'POST'])
def api_switch(n, action):
    """GET as well as POST, deliberately: a student can drive a relay by typing
    a URL into a phone browser, which is a good first lesson in what the
    dashboard's buttons are actually doing. Don't copy that onto a real network."""
    if n not in (1, 2) or action not in VALID_ACTIONS:
        return jsonify(ok=False, error='bad relay or action'), 400
    topic = f'{DEVICE}/switch{n}/set'
    _publish(topic, action)
    return jsonify(ok=True, topic=topic, payload=action)


@app.route('/api/request/<what>', methods=['GET', 'POST'])
def api_request(what):
    if what not in VALID_REQUESTS:
        return jsonify(ok=False, error='unknown request'), 400
    topic = f'{DEVICE}/request'
    _publish(topic, what)
    return jsonify(ok=True, topic=topic, payload=what)


if __name__ == '__main__':
    # use_reloader=False matters: the reloader runs the module in two processes,
    # which would open two MQTT connections with the same client_id and the
    # broker would kick each in turn, forever. In production gunicorn imports
    # this once and the question doesn't arise.
    app.run(host='0.0.0.0', port=5000, use_reloader=False)
