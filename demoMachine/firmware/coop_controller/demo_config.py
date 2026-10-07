# demo_config.py — demoMachine rig settings for the coop controller demo.
#
# DELIBERATELY NOT SECRET, and deliberately not called secrets.py.
#
# The home-lab firmware this is ported from keeps WiFi and MQTT credentials in a
# gitignored secrets.py. That pattern is load-bearing there and would be theatre
# here: the hotspot PSK and the mqtt/mqtt broker login are already printed in the
# demoMachine README, the rig is an isolated offline island with nothing on it
# worth taking, and students need to read these values to understand how a device
# finds its broker. Hiding them would teach the wrong lesson and break the "flash
# it and it just joins" property the demo depends on.
#
# Do not copy this file's approach to anything on a real network.

# ─── Hotspot (the Pi4's own AP — see demoMachine/README.md) ──────────────────
WIFI_SSID     = 'demomachine'
WIFI_PASSWORD = '818pierce'

# ─── Broker ──────────────────────────────────────────────────────────────────
# A literal address, not a name. The hotspot's dnsmasq hands out leases but does
# not resolve the Pi's own hostname, so there is no 'mqtt.lan' equivalent here —
# 192.168.4.1 is the AP's static address and is the one thing guaranteed to exist.
MQTT_BROKER   = '192.168.4.1'
MQTT_PORT     = 1883
MQTT_USER     = 'mqtt'
MQTT_PASSWORD = 'mqtt'

# ─── Probe calibration ───────────────────────────────────────────────────────
# Offset-only, applied to the DS18B20 reading before publishing. 0.0 = raw.
# The home lab calibrates probes on a transfer jig and folds the result in here;
# for the demo it is a one-number knob a student can turn to see the published
# value move, which is most of what calibration feels like.
TEMP_OFFSET_C = 0.0
