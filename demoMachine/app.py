"""
Pi4 IoT Dashboard - Flask + MQTT
Requires: pip install flask flask-socketio paho-mqtt
Run with: python app.py
"""

import queue
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iot-dashboard-secret'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

# ── MQTT Configuration ────────────────────────────────────────────────────────
MQTT_BROKER = '127.0.0.1'
MQTT_PORT   = 1883
MQTT_USER   = 'mqtt'
MQTT_PASS   = 'mqtt'

SUBSCRIBE_TOPICS = [
    'jumilla/picow_cotroller_hat_1/switch1/state',
    'jumilla/picow_cotroller_hat_1/switch2/state',
    'jumilla/picow_cotroller_hat_1/status',
    'jumilla/temp_sensor/jumilla_weatherstation1',
    'jumilla/shed/log/output',
]

# ── Shared State ──────────────────────────────────────────────────────────────
device_state = {
    'switch1': 'unknown',
    'switch2': 'unknown',
    'status':  'unknown',
    'temperature': '--',
    'log': '',
    'last_seen': None,
    'feed': []
}
state_lock = threading.Lock()

# Queue for safely passing messages from MQTT thread to SocketIO
mqtt_queue = queue.Queue()

# ── MQTT Client ───────────────────────────────────────────────────────────────
mqtt_client = mqtt.Client(client_id='pi4_dashboard', protocol=mqtt.MQTTv311)

def mqtt_on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Dashboard MQTT connected.')
        for topic in SUBSCRIBE_TOPICS:
            client.subscribe(topic, qos=1)
    else:
        print(f'MQTT connect failed, rc={rc}')

def mqtt_on_message(client, userdata, msg):
    # Just put on queue - never call socketio from this thread
    mqtt_queue.put((msg.topic, msg.payload.decode('utf-8', errors='replace')))

def process_mqtt_queue():
    """Dedicated thread: drains queue and emits to all browsers via SocketIO."""
    while True:
        try:
            topic, payload = mqtt_queue.get(timeout=1)
            ts = datetime.now().strftime('%H:%M:%S')

            with state_lock:
                if topic == 'jumilla/picow_cotroller_hat_1/switch1/state':
                    device_state['switch1'] = payload
                elif topic == 'jumilla/picow_cotroller_hat_1/switch2/state':
                    device_state['switch2'] = payload
                elif topic == 'jumilla/picow_cotroller_hat_1/status':
                    device_state['status'] = payload
                elif topic == 'jumilla/temp_sensor/jumilla_weatherstation1':
                    device_state['temperature'] = payload
                elif topic == 'jumilla/shed/log/output':
                    device_state['log'] = payload

                device_state['last_seen'] = ts
                parts = topic.split('/')
                short_topic = parts[-1]
                if short_topic == 'state' and len(parts) >= 3:
                    short_topic = parts[-2] + '/state' 
                entry = {'time': ts, 'topic': short_topic, 'value': payload[:80]}
                device_state['feed'].insert(0, entry)
                device_state['feed'] = device_state['feed'][:50]
                state_snapshot = dict(device_state)

            socketio.emit('mqtt_update', {
                'topic':   topic,
                'payload': payload,
                'ts':      ts,
                'state':   state_snapshot
            }, namespace='/')

        except queue.Empty:
            continue
        except Exception as e:
            print(f'Queue processor error: {e}')

def publish(topic, payload):
    mqtt_client.publish(topic, payload, qos=1)

def start_mqtt():
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.on_connect = mqtt_on_connect
    mqtt_client.on_message = mqtt_on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    with state_lock:
        state = dict(device_state)
    return render_template_string(HTML_TEMPLATE, state=state)

# ── Socket.IO events ──────────────────────────────────────────────────────────
@socketio.on('command')
def handle_command(data):
    action = data.get('action')
    topic_map = {
        'sw1_on':       ('jumilla/picow_cotroller_hat_1/switch1/set', 'on'),
        'sw1_off':      ('jumilla/picow_cotroller_hat_1/switch1/set', 'off'),
        'sw2_on':       ('jumilla/picow_cotroller_hat_1/switch2/set', 'on'),
        'sw2_off':      ('jumilla/picow_cotroller_hat_1/switch2/set', 'off'),
        'log_request':  ('jumilla/shed/log/request', '1'),
        'log_clear':    ('jumilla/shed/log/clear', '1'),
        'test_log':     ('jumilla/shed/test_logging', '1'),
        'temp_request': ('jumilla/temp_sensor/request/jumilla_weatherstation1', '1'),
    }
    if action in topic_map:
        topic, msg = topic_map[action]
        publish(topic, msg)
        emit('command_ack', {'action': action, 'topic': topic, 'msg': msg})

@socketio.on('connect')
def on_connect():
    with state_lock:
        emit('mqtt_update', {'state': dict(device_state)})

# ── HTML Template ─────────────────────────────────────────────────────────────
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jumilla IoT Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:      #0a0c10;
    --surface: #111520;
    --border:  #1e2840;
    --accent:  #00d4ff;
    --green:   #00ff88;
    --red:     #ff3366;
    --amber:   #ffb300;
    --text:    #c8d8f0;
    --muted:   #4a5878;
    --glow:    0 0 12px rgba(0,212,255,.35);
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Rajdhani', sans-serif;
    font-weight: 500;
    min-height: 100vh;
    background-image:
      repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(0,212,255,.04) 39px, rgba(0,212,255,.04) 40px),
      repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(0,212,255,.04) 39px, rgba(0,212,255,.04) 40px);
  }
  header {
    display: flex; align-items: center; gap: 1rem;
    padding: 1rem 2rem;
    border-bottom: 1px solid var(--border);
    background: rgba(17,21,32,.9);
    backdrop-filter: blur(8px);
    position: sticky; top: 0; z-index: 100;
  }
  header h1 {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.2rem; letter-spacing: .12em;
    color: var(--accent); text-transform: uppercase;
  }
  .status-pill {
    margin-left: auto; padding: .25rem .75rem;
    border-radius: 999px; font-size: .8rem; letter-spacing: .1em;
    font-family: 'Share Tech Mono', monospace;
    border: 1px solid var(--muted); color: var(--muted);
    transition: all .4s;
  }
  .status-pill.online  { border-color: var(--green); color: var(--green); box-shadow: 0 0 8px rgba(0,255,136,.3); }
  .status-pill.offline { border-color: var(--red);   color: var(--red); }
  main { max-width: 1100px; margin: 0 auto; padding: 2rem; display: grid; gap: 1.5rem; }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px; padding: 1.5rem;
    position: relative; overflow: hidden;
  }
  .card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: .5;
  }
  .card-title {
    font-size: .75rem; letter-spacing: .15em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 1rem;
    font-family: 'Share Tech Mono', monospace;
  }
  .relay-name { font-size: 1.4rem; font-weight: 700; margin-bottom: .5rem; }
  .relay-state {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.1rem; margin-bottom: 1.2rem; transition: color .3s;
  }
  .relay-state.on      { color: var(--green); }
  .relay-state.off     { color: var(--red); }
  .relay-state.unknown { color: var(--muted); }
  .btn-row { display: flex; gap: .75rem; }
  .btn {
    flex: 1; padding: .6rem 1rem; border: none; cursor: pointer;
    font-family: 'Rajdhani', sans-serif; font-size: 1rem; font-weight: 700;
    letter-spacing: .1em; border-radius: 2px;
    text-transform: uppercase; transition: all .2s;
  }
  .btn-on  { background: rgba(0,255,136,.12); color: var(--green); border: 1px solid rgba(0,255,136,.4); }
  .btn-off { background: rgba(255,51,102,.12); color: var(--red);   border: 1px solid rgba(255,51,102,.4); }
  .btn-on:hover  { background: rgba(0,255,136,.25); box-shadow: 0 0 10px rgba(0,255,136,.3); }
  .btn-off:hover { background: rgba(255,51,102,.25); box-shadow: 0 0 10px rgba(255,51,102,.3); }
  .btn-action {
    width: 100%; background: rgba(0,212,255,.08); color: var(--accent);
    border: 1px solid rgba(0,212,255,.3); padding: .6rem 1rem; margin-bottom: .5rem;
  }
  .btn-action:hover { background: rgba(0,212,255,.18); box-shadow: var(--glow); }
  .btn-warn { background: rgba(255,179,0,.08); color: var(--amber); border: 1px solid rgba(255,179,0,.3); }
  .btn-warn:hover { background: rgba(255,179,0,.2); }
  .temp-value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 3rem; color: var(--accent);
    letter-spacing: .05em; line-height: 1; margin-bottom: .25rem;
  }
  .temp-unit { font-size: 1.2rem; color: var(--muted); margin-bottom: 1rem; }
  .feed { height: 220px; overflow-y: auto; font-family: 'Share Tech Mono', monospace; font-size: .78rem; }
  .feed::-webkit-scrollbar { width: 4px; }
  .feed::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
  .feed-row {
    display: grid; grid-template-columns: 5rem 1fr auto;
    gap: .5rem; padding: .3rem 0;
    border-bottom: 1px solid rgba(30,40,64,.6);
    animation: fadeIn .2s ease;
  }
  @keyframes fadeIn { from { opacity:0; transform: translateY(-4px); } to { opacity:1; transform:none; } }
  .feed-time  { color: var(--muted); }
  .feed-topic { color: var(--accent); }
  .feed-value { color: var(--text); text-align: right; }
  .log-box {
    background: #060810; border: 1px solid var(--border);
    border-radius: 2px; padding: 1rem;
    font-family: 'Share Tech Mono', monospace; font-size: .78rem;
    line-height: 1.6; color: #7a9abf;
    white-space: pre-wrap; word-break: break-all;
    height: 200px; overflow-y: auto;
  }
  @keyframes pulse-border {
    0%   { border-color: var(--accent); box-shadow: 0 0 16px rgba(0,212,255,.5); }
    100% { border-color: var(--border); box-shadow: none; }
  }
  .card.flash { animation: pulse-border .7s ease-out forwards; }
  .dot { display:inline-block; width:.55rem; height:.55rem; border-radius:50%; margin-right:.4rem; background: var(--muted); }
  .dot.online  { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot.offline { background: var(--red); }
</style>
</head>
<body>
<header>
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <rect x="1" y="1" width="26" height="26" rx="2" stroke="#00d4ff" stroke-width="1.5"/>
    <circle cx="14" cy="14" r="5" stroke="#00d4ff" stroke-width="1.5"/>
    <line x1="14" y1="1" x2="14" y2="9" stroke="#00d4ff" stroke-width="1.5"/>
    <line x1="14" y1="19" x2="14" y2="27" stroke="#00d4ff" stroke-width="1.5"/>
    <line x1="1" y1="14" x2="9" y2="14" stroke="#00d4ff" stroke-width="1.5"/>
    <line x1="19" y1="14" x2="27" y2="14" stroke="#00d4ff" stroke-width="1.5"/>
  </svg>
  <h1>Jumilla&nbsp;&nbsp;IoT&nbsp;&nbsp;Dashboard</h1>
  <div class="status-pill" id="device-status">
    <span class="dot" id="status-dot"></span>
    <span id="status-text">CONNECTING…</span>
  </div>
</header>

<main>
  <div class="grid-2">
    <div class="card" id="card-sw1">
      <div class="card-title">// Relay 01</div>
      <div class="relay-name">Switch 1</div>
      <div class="relay-state unknown" id="sw1-state">● UNKNOWN</div>
      <div class="btn-row">
        <button class="btn btn-on"  onclick="cmd('sw1_on')">ON</button>
        <button class="btn btn-off" onclick="cmd('sw1_off')">OFF</button>
      </div>
    </div>
    <div class="card" id="card-sw2">
      <div class="card-title">// Relay 02</div>
      <div class="relay-name">Switch 2</div>
      <div class="relay-state unknown" id="sw2-state">● UNKNOWN</div>
      <div class="btn-row">
        <button class="btn btn-on"  onclick="cmd('sw2_on')">ON</button>
        <button class="btn btn-off" onclick="cmd('sw2_off')">OFF</button>
      </div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card" id="card-temp">
      <div class="card-title">// Temperature Sensor</div>
      <div class="temp-value" id="temp-val">{{ state.temperature }}</div>
      <div class="temp-unit">°C  ·  ds18b20</div>
      <button class="btn btn-action" onclick="cmd('temp_request')">REQUEST READING</button>
    </div>
    <div class="card">
      <div class="card-title">// Device Actions</div>
      <button class="btn btn-action" onclick="cmd('log_request')">DUMP LOG → MQTT</button>
      <button class="btn btn-action btn-warn" onclick="cmd('log_clear')">CLEAR LOG</button>
      <button class="btn btn-action" onclick="cmd('test_log')">TEST LOGGING</button>
      <div id="ack-msg" style="margin-top:.75rem; font-family:'Share Tech Mono',monospace; font-size:.75rem; color:var(--muted); min-height:1.2em;"></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">// Live Activity Feed &nbsp;<span style="color:var(--muted);font-size:.7rem;" id="last-seen"></span></div>
    <div class="feed" id="feed">
      <div style="color:var(--muted); padding:.5rem 0; font-family:'Share Tech Mono',monospace; font-size:.8rem;">Waiting for MQTT messages…</div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">// Device Log</div>
    <div class="log-box" id="log-box">No log data received yet.</div>
  </div>
</main>

<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<script>
  // Force WebSocket only - skip long-polling which causes the delays
  const socket = io({ transports: ['websocket'], upgrade: false });

  socket.on('connect',    () => console.log('SocketIO connected via WebSocket'));
  socket.on('disconnect', () => console.log('SocketIO disconnected'));

  function applyState(state) {
    setSwitchUI('sw1', state.switch1);
    setSwitchUI('sw2', state.switch2);

    const s = (state.status || 'unknown').toLowerCase();
    document.getElementById('device-status').className = 'status-pill ' + s;
    document.getElementById('status-dot').className    = 'dot ' + s;
    document.getElementById('status-text').textContent = s.toUpperCase();

    if (state.temperature) document.getElementById('temp-val').textContent = state.temperature;
    if (state.log) {
      const lb = document.getElementById('log-box');
      lb.textContent = state.log;
      lb.scrollTop = lb.scrollHeight;
    }
    if (state.feed && state.feed.length) renderFeed(state.feed);
    if (state.last_seen) document.getElementById('last-seen').textContent = 'last msg ' + state.last_seen;
  }

  function setSwitchUI(sw, val) {
    const el = document.getElementById(sw + '-state');
    if (!el) return;
    const v = (val || 'unknown').toLowerCase();
    el.textContent = '● ' + v.toUpperCase();
    el.className = 'relay-state ' + v;
  }

  function renderFeed(feed) {
    document.getElementById('feed').innerHTML = feed.map(e =>
      `<div class="feed-row">
        <span class="feed-time">${e.time}</span>
        <span class="feed-topic">${e.topic}</span>
        <span class="feed-value">${e.value}</span>
      </div>`
    ).join('');
  }

  socket.on('mqtt_update', data => {
    if (data.state) applyState(data.state);
    const topic = data.topic || '';
    let cardId = null;
    if (topic.includes('switch1'))      cardId = 'card-sw1';
    else if (topic.includes('switch2')) cardId = 'card-sw2';
    else if (topic.includes('temp'))    cardId = 'card-temp';
    if (cardId) {
      const card = document.getElementById(cardId);
      card.classList.remove('flash');
      void card.offsetWidth;
      card.classList.add('flash');
    }
  });

  function cmd(action) { socket.emit('command', { action }); }

  socket.on('command_ack', data => {
    const ack = document.getElementById('ack-msg');
    ack.textContent = '▶ ' + data.topic + ' → ' + data.msg;
    setTimeout(() => { ack.textContent = ''; }, 3000);
  });
</script>
</body>
</html>'''

# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    start_mqtt()

    processor = threading.Thread(target=process_mqtt_queue, daemon=True)
    processor.start()

    print("Starting IoT Dashboard on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
