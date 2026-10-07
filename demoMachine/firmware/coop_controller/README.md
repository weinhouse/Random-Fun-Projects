# Coop Controller — demoMachine firmware

A Pico W demo of the chicken coop controller: two relays, a door sensor, and a
temperature probe, talking MQTT straight to the demoMachine broker. No Home
Assistant, no cloud, no internet — the rig is a self-contained island.

It is a MicroPython port of the home lab's ESPHome coop firmware, so the demo
behaves like the real board. The teaching point is the **poor man's PLC** shape:
the Pico is the PLC (it owns the I/O and the logic), the broker is the fieldbus,
and the Flask dashboard is the HMI (a view, never the authority).

```
 buttons ─┐                    ┌─ relays
 door  ───┤   Pico W (PLC)  ───┤          ──MQTT──► Mosquitto ──► Flask HMI
 probe ───┘                    └─ OLED                 ▲             (browser)
                                                       └── mosquitto_sub on a laptop
```

## Hardware

The same arrangement as the real coop board, so a hat built for the coop drops
straight on. The **Seengreat Pico Expansion Plus** is a carrier with three
Pico-compatible headers wired in parallel — not a vertical stack. Three boards
sit side by side on it:

| Header | Board | Carries |
|--------|-------|---------|
| 1 | Pico W | the MCU itself |
| 2 | Relay hat | the two relays, GP6 / GP7, each with its own indicator LED |
| 3 | Custom coop sensor hat | optocoupler input, two buttons, 7-pin OLED header (J1) |

**The OLED breakout lives on the coop hat, not the carrier.** All seven lines
come off the hat's J1 header — ground, 3V3, and five signals — so the display
plugs straight in with no flying wire. The carrier has an OLED header of its own
and it is deliberately unused, because it omits the reset line:

| J1 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|----|---|---|---|---|---|---|---|
| | GND | 3V3 | GP14 sck | GP15 mosi | GP26 res | GP12 dc | GP13 cs |

(Verified against `ChickenCoopController.fzz` with `tools/fritzing/fzz_netlist.py`
from the home repo.)

The header labels on the hat are the *silicon* SPI1 function names. GP12 is SPI1
RX (MISO), but the SH1106 is write-only, so that pad is reused as **DC** — wire
to the label, configure as DC.

The carrier's Grove ports are still used for one thing: the DS18B20 daughter
board.

Because the headers are parallel rather than stacked, every GPIO is shared by all
three boards — which is exactly why the pin map below has to be respected rather
than negotiated. Two boards driving one pin is a short, not a conflict message.

### Pin map

| GPIO | Use |
|------|-----|
| 2 | Safe-mode jumper — tie to GND to disable the watchdog while on USB |
| 4 | Door input, through the hat's optocoupler (10k pull-up R2 to 3V3) |
| 6, 7 | Relay 1, Relay 2 — active HIGH |
| 8, 9 | Button 2, Button 1 — 0.1 µF RC debounce on the hat |
| 12–15, 26 | OLED SH1106 on SPI1, via J1 **on the sensor hat** — dc=12, cs=13, sck=14, mosi=15, res=26 |
| 27 | DS18B20 one-wire, single probe (needs a 4.7k pull-up to 3V3) |

### The demo door

The real coop uses a 24 V inductive proximity switch that sees the closed door.
On the bench, a **button feeding 24 V into the hat's sensor JST** does the same
job electrically, so the firmware is unchanged and the polarity is the real one:

```
button pressed  →  24V at the JST  →  opto LED lit  →  phototransistor conducts
                →  GP4 pulled LOW  →  "target present"  →  DOOR CLOSED
button released →  GP4 pulled HIGH by R2  →  no target  →  DOOR OPEN
```

**Holding the button = coop shut.** GP4 is pulled high and the sensor pulls it
low; nothing is inverted anywhere in the firmware. The whole mapping is one
function, `door_state()`.

## Files

Copy all five to the Pico's filesystem root:

| File | |
|------|---|
| `demo_coop_controller.py` | the firmware |
| `demo_config.py` | SSID, PSK, broker, MQTT login, probe offset |
| `oled_manager_large_screen_rev.py` | eight-line OLED renderer (`rotate=180`) |
| `sh1106.py` | display driver |
| `mqtt_as.py` | async MQTT client — see provenance below |

`onewire.py` and `ds18x20.py` ship frozen into the official Pico W build, so
there is nothing to copy for the probe. Confirm on a fresh board with
`import onewire, ds18x20` at the REPL before assuming it.

### Flashing a fresh Pico W

1. Install MicroPython: hold **BOOTSEL** while plugging in, the board appears as
   an `RPI-RP2` drive, drop the Pico **W** `.uf2` on it. It reboots to a REPL.
2. Copy the files and give it a `main.py` so it starts on power alone — which is
   what you want when the demo is just plugged into a USB brick:

```bash
cd firmware/coop_controller
for f in mqtt_as.py sh1106.py oled_manager_large_screen_rev.py \
         demo_config.py demo_coop_controller.py; do
    mpremote cp "$f" ":$f"
done
echo 'import demo_coop_controller' > /tmp/main.py
mpremote cp /tmp/main.py :main.py
mpremote reset
```

A one-line `main.py` rather than renaming the firmware, so the board still shows
a readable filename when a student opens it in Thonny.

3. Watch it come up: `mpremote repl` (Ctrl-] to leave). The splash shows the
   reset cause, whether the watchdog armed, and `DS:yes` / `DS:NO` for the probe
   — a wrong one-wire pin or a missing 4.7k pull-up reads as "no probe" with no
   error anywhere, so it is worth two seconds of screen.

**Ground GPIO 2 for bench work.** The watchdog resets the board if the asyncio
scheduler stops running, which is unhelpful while you are sitting at the REPL.

## Topics

Device base: `demo/coop_1`. Everything a widget reads is published **retained**,
so the dashboard renders instantly on page load and never has to ask.

| Topic | |
|-------|---|
| `status` | `online` / `offline` — the second one is the broker's, via LWT |
| `switch1/state`, `switch2/state` | `on` / `off` |
| `door` | `open` / `closed` |
| `temp_c` | one decimal; **empty payload = no probe** (deletes the retained value) |
| `reset_cause` | why the board last restarted |
| `wifi` | `{"rssi":-54,"quality":"good"}`, every 60 s |
| `health` | uptime, free memory, pin counters, subsystem ages, every 60 s |
| `log` | human-readable events as they happen |
| `response` | replies to `request` |

Subscribed: `switch1/set` and `switch2/set` take `on` / `off` / `toggle`;
`request` takes `ping` / `state` / `health` / `pins` / `reset`.

Watch the whole conversation from any laptop on the hotspot:

```bash
mosquitto_sub -h 192.168.4.1 -u mqtt -P mqtt -t 'demo/#' -v
```

Drive it by hand, which is the fastest way to show that the dashboard is just
another client:

```bash
mosquitto_pub -h 192.168.4.1 -u mqtt -P mqtt -t 'demo/coop_1/switch1/set' -m toggle
mosquitto_pub -h 192.168.4.1 -u mqtt -P mqtt -t 'demo/coop_1/request'     -m ping
```

### A demo worth doing on purpose

Publish a lie and then watch it get corrected:

```bash
mosquitto_pub -h 192.168.4.1 -u mqtt -P mqtt -r -t 'demo/coop_1/switch1/state' -m on
```

The broker now retains `on` and the dashboard lamp lights, while the relay is
still physically off — the HMI is showing someone's opinion, not the hardware.
Press **Resync** on the dashboard (or publish `state` to `request`) and the Pico
republishes from the actual pins. That is the entire argument for why state lives
in the firmware rather than in the app.

## Bench checks

Four things, in this order:

1. **Door polarity** — press the 24 V button, screen should read `Door: CLOSED`
   and `demo/coop_1/door` should publish `closed`.
2. **OLED rotation** — `rotate=0` in `OLEDManager.__init__` is the verified value
   for this rig (checked 2026-10-07).

   The ESPHome coop build wants `rotation: 180°` for the same display in the same
   header, and that is a **library** difference, not a hardware one. SH1106
   orientation comes from two registers — segment remap and COM scan direction —
   and `sh1106.py` and ESPHome disagree about which combination is zero, so
   `sh1106.py`'s `rotate=0` is ESPHome's `180°`. On any board in this family:
   **MicroPython `rotate` = ESPHome `rotation` − 180**. Don't go looking at the
   connector.
3. **Buttons → relays** — button 1 toggles relay 1, button 2 toggles relay 2, and
   each publishes its new state. The relay hat has an indicator LED per channel,
   so you get the answer three ways at once: the LED, the audible click, and the
   dashboard lamp. **If the LED is lit while the dashboard says `off`, the relay
   hat is active LOW** — invert in `apply_relay()` and in the two
   `Pin(..., value=0)` constructors, and nothing else changes.

   Those LEDs are also what makes this a good first demo at a table: a student
   can press a physical button, watch the LED and hear the click, and see a
   browser on their own phone update half a second later — with the MQTT message
   that carried it visible in the traffic pane. The whole chain, in one glance.
4. **Temperature** — hold the probe and watch the published value move.

## Divergences from the ESPHome coop build

The YAML gets a lot for free that has to be hand-rolled here, and a few things
are deliberately different *because* this is a demo rig:

| | ESPHome coop board | This demo |
|---|---|---|
| Transport | native API to Home Assistant | plain MQTT to Mosquitto |
| State after reboot | `restore_mode: RESTORE_DEFAULT_OFF` | relays always come up OFF — no persistence on a Pico |
| Who holds state | Home Assistant | the broker's retained set, refilled by the firmware on every reconnect |
| Button debounce | `delayed_off: 100ms` filter | falling-edge IRQ, fire then ignore 100 ms |
| Door debounce | `delayed_on` + `delayed_off` | both-edge IRQ arms a 100 ms settle task, which then **reads the pin** — so a missed edge can't invert the state |
| Door drift | n/a | the pin is re-read every 60 s and republished only on disagreement — an event stream with no reconciliation drifts |
| Probe filtering | `median` + `filter_out` | rolling median of 3, `85.0` / `-127.0` rejected |
| Watchdog | ESPHome's own | 8 s hardware WDT fed only while wifi/health/gc check in |
| Display | sized Roboto, 4 big lines | built-in 8×8 font, 8 small lines (framebuf has no other font) |
| Credentials | `!secret` from `secrets.yaml` | in the clear in `demo_config.py`, on purpose — see the file header |

Two watchdog omissions are specific to this rig and worth knowing about:

- **`temp` is not critical.** The home firmware demands a successful probe read
  every 15 minutes. Here the probe is a plug-in accessory, and a board that
  hard-resets every 15 minutes because nothing is plugged in teaches nothing.
- **`mqtt` is not critical.** The home firmware demands a qos1 PUBACK every 180 s,
  which self-heals a wedged socket. But on this rig the broker is the subject of
  the lesson and *will* be stopped and restarted — with `mqtt` critical, every one
  of those restarts reboot-loops the Pico. `mqtt_as` reconnects on its own; for a
  genuine wedge there is the `reset` request and a USB cable.

What is left guards the one thing nothing else can recover from: a frozen asyncio
scheduler. If even that proves more trouble than it's worth on a demo, ground
GPIO 2 permanently or delete the `if wdt_enabled:` block in `main()`.

## `mqtt_as.py` provenance

Vendored byte-exact from
[peterhinch/micropython-mqtt](https://github.com/peterhinch/micropython-mqtt),
`mqtt_as/__init__.py` at **VERSION (0, 8, 5)**, saved here as a single
`mqtt_as.py` (importing it as a module file works identically).

Vendored rather than fetched because the rig is offline — nobody can
`pip`/`mip` anything at the table. If you want the exact copy the home-lab Picos
are running instead, pull it off one of them: `mpremote cp :mqtt_as.py ./mqtt_as.py`.

## Dashboard side

`demo_app/app.py` holds one persistent MQTT subscriber and serves the HMI. It
needs paho, which the firmware does not:

```bash
# with ethernet plugged in — there is no internet on the hotspot
source ~/demo_app/venv/bin/activate && pip install paho-mqtt
sudo systemctl restart demomachine
journalctl -u demomachine.service -f
```

The app is **push-fed** by MQTT and the browser polls it every 500 ms, so the
only lag between a relay clicking and the lamp moving is that half second. One
gunicorn worker is required — `--threads 4` is fine, `--workers 2` would give you
two independent caches and a dashboard that contradicts itself. The reason is
written out at the top of `app.py`.
