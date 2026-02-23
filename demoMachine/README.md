# Pi4 IoT Dashboard

A Raspberry Pi 4B configured as a self-contained IoT demo device. The Pi4 acts as a WiFi hotspot, runs a Mosquitto MQTT broker, and serves a real-time Flask web dashboard. IoT devices (Pico W microcontrollers) connect to the hotspot, communicate via MQTT, and are monitored and controlled through the web dashboard.

---

## Hardware

- Raspberry Pi 4B
- USB WiFi adapter — **Ralink RT5370** (required — onboard BCM4345 has a known AP mode driver bug on kernel 6.12)
- IoT device: Raspberry Pi Pico W running MicroPython with `mqtt_as` library

---

## Architecture

```
[ Pico W ] ──MQTT──> [ Mosquitto on Pi4 ] <──> [ Flask Dashboard ]
     |                                                   |
     └──────── WiFi (wlan1 hotspot) ───────────── [ Browser / Phone ]
```

- `wlan1` (USB adapter) — hotspot broadcasting the demo network
- `wlan0` (onboard) — connects to venue/home WiFi for internet if needed
- `eth0` — DHCP ethernet, available if plugged in
- Mosquitto — MQTT broker on `localhost:1883`
- Flask + Socket.IO — real-time web dashboard on port `5000`

---

## OS & Networking

**OS:** Raspberry Pi OS (Debian 13 Trixie, 64-bit)  
**Network manager:** NetworkManager (with netplan as renderer)

### Key config file locations

| What | Where |
|---|---|
| Hotspot connection | `/etc/NetworkManager/system-connections/hotspot.nmconnection` |
| eth0 + wlan0 (home WiFi) | `/etc/netplan/*.yaml` |
| NetworkManager main config | `/etc/NetworkManager/NetworkManager.conf` |

### Important fix applied during setup

`/etc/NetworkManager/NetworkManager.conf` — changed `managed=false` to `managed=true` in the `[ifupdown]` section. Without this, NetworkManager treats all interfaces as unmanaged and the hotspot cannot be configured.

---

## WiFi Hotspot Setup

The hotspot is managed entirely by NetworkManager using `ipv4.method shared`. This handles IP assignment, DHCP for connected clients, and routing — no separate `hostapd` or `dnsmasq` installation needed.

```bash
sudo nmcli con add \
  type wifi \
  ifname wlan1 \
  con-name hotspot \
  ssid "your-ssid" \
  mode ap \
  ipv4.method shared \
  ipv4.addresses 192.168.4.1/24 \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "your-password" \
  802-11-wireless.band bg \
  802-11-wireless.channel 6

sudo nmcli con modify hotspot connection.autoconnect yes
sudo nmcli con up hotspot
```

The hotspot survives reboots automatically via NetworkManager autoconnect.

### Verify hotspot is running

```bash
nmcli device status
ip addr show wlan1   # should show 192.168.4.1
```

### Why not the onboard WiFi chip?

The BCM4345 chip (`brcmfmac` driver) on Pi4 has a known bug on kernel 6.12 — `brcmf_vif_set_mgmt_ie: vndr ie set error -52` — that prevents client devices from associating in AP mode. The Ralink RT5370 USB adapter works plug-and-play with no issues.

---

## Changing the Home WiFi Network (wlan0)

`wlan0` is configured via netplan. To change to a different network at a new location:

```bash
sudo nano /etc/netplan/*.yaml
```

Update the SSID and password (plain text is fine — netplan hashes it internally):

```yaml
network:
  version: 2
  renderer: NetworkManager
  wifis:
    wlan0:
      access-points:
        "NewNetworkSSID":
          password: "plainpassword"
      dhcp4: true
```

Apply immediately (no reboot needed):

```bash
sudo netplan apply
```

> **Note:** If you lose SSH access after a bad netplan change, the Pi4 is still reachable via the hotspot at `192.168.4.1`.

---

## Mosquitto MQTT Broker

```bash
sudo apt install -y mosquitto mosquitto-clients
```

Config at `/etc/mosquitto/conf.d/local.conf`:

```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

Create the MQTT user:

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd mqtt
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
sudo chmod 640 /etc/mosquitto/passwd
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto
```

Test:

```bash
mosquitto_sub -h localhost -u mqtt -P mqtt -t test &
mosquitto_pub -h localhost -u mqtt -P mqtt -t test -m "hello"
```

---

## Flask Dashboard

### Install

```bash
mkdir -p ~/dashboard && cd ~/dashboard
python3 -m venv venv
source venv/bin/activate
pip install flask flask-socketio paho-mqtt
```

Copy `app.py` to `~/dashboard/` and run:

```bash
python app.py
```

Dashboard available at `http://192.168.4.1:5000` from any device connected to the hotspot.

### Run as a systemd service (auto-start on boot)

```bash
sudo tee /etc/systemd/system/iot-dashboard.service <<EOF
[Unit]
Description=IoT Flask Dashboard
After=network.target mosquitto.service

[Service]
User=pi
WorkingDirectory=/home/pi/dashboard
ExecStart=/home/pi/dashboard/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable iot-dashboard
sudo systemctl start iot-dashboard
```

### Architecture notes

The dashboard uses three threads:
- **MQTT thread** (`paho loop_start()`) — receives messages, puts them on a `queue.Queue()`
- **Queue processor thread** — drains the queue, updates shared state, emits via Socket.IO
- **Flask/SocketIO thread** — serves HTTP and WebSocket connections

The browser JS connects via WebSocket only (`transports: ['websocket']`) to avoid long-polling delays.

---

## MQTT Topic Reference

### Dashboard publishes → Pico W receives (commands)

| Topic | Payload | Effect |
|---|---|---|
| `jumilla/picow_cotroller_hat_1/switch1/set` | `on` / `off` | Toggle Relay 1 |
| `jumilla/picow_cotroller_hat_1/switch2/set` | `on` / `off` | Toggle Relay 2 |
| `jumilla/temp_sensor/request/jumilla_weatherstation1` | `1` | Request temperature reading |
| `jumilla/shed/log/request` | `1` | Dump device log to MQTT |
| `jumilla/shed/log/clear` | `1` | Rotate and clear device log |
| `jumilla/shed/test_logging` | `1` | Send a test log entry |

### Pico W publishes → Dashboard receives (telemetry)

| Topic | Values | Description |
|---|---|---|
| `jumilla/picow_cotroller_hat_1/switch1/state` | `on` / `off` | Relay 1 state |
| `jumilla/picow_cotroller_hat_1/switch2/state` | `on` / `off` | Relay 2 state |
| `jumilla/picow_cotroller_hat_1/status` | `online` / `offline` | Device LWT status |
| `jumilla/temp_sensor/jumilla_weatherstation1` | float string | Temperature in °C |
| `jumilla/shed/log/output` | text | Device error log content |

---

## Pico W Configuration

In `controller_hat_proto_1_rev.py`, set the broker to the Pi4 hotspot IP:

```python
config['ssid']     = 'your-hotspot-ssid'
config['wifi_pw']  = 'your-hotspot-password'
config['server']   = '192.168.4.1'   # Pi4 hotspot IP
config['user']     = 'mqtt'
config['password'] = 'mqtt'
```

---

## Troubleshooting Notes

### hotspot shows as unmanaged
Edit `/etc/NetworkManager/NetworkManager.conf` and set `managed=true` in `[ifupdown]`.

### hotspot won't activate / wrong interface
```bash
sudo nmcli con modify hotspot connection.interface-name wlan1
sudo nmcli con down hotspot && sudo nmcli con up hotspot
```

### Mosquitto fails to start (exit code 13)
Check password file permissions:
```bash
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
sudo chmod 640 /etc/mosquitto/passwd
```

### Dashboard updates are slow
Ensure the browser is connecting via WebSocket not long-polling. Check browser console for `SocketIO connected via WebSocket`. The JS client should have `transports: ['websocket']` set.

---

## Files

| File | Description |
|---|---|
| `app.py` | Flask + Socket.IO dashboard with MQTT integration |
| `controller_hat_proto_1_rev.py` | MicroPython firmware for the Pico W control panel |
