"""
demo_coop_controller.py
demoMachine demo — Chicken Coop Controller as a poor man's PLC.

A MicroPython port of the home lab's ESPHome coop firmware
(~/code/esphome/chicken-coop-controller.yaml), re-pointed at the demoMachine
hotspot and its Mosquitto broker. There is no Home Assistant anywhere in the
path: the Pico talks MQTT directly, and the Flask dashboard on the Pi is a pure
HMI reading the same topics.

Board stack (bottom to top):
  Seengreat Pico Expansion Plus  — Pico sits here, brings out SPI1 + Grove
  Pico switch hat                — the two relays, GP6 / GP7
  Custom coop sensor hat         — optocoupler input, two buttons, 7-pin OLED J1

Pins in use:
  GPIO 2          safe mode (jumper to GND disables the WDT — use on the bench)
  GPIO 4          door input, via the hat's optocoupler (10k pull-up R2 on hat)
  GPIO 6, 7       relay 1, relay 2 (active HIGH)
  GPIO 8, 9       button 2, button 1 (RC-debounced on the hat)
  GPIO 12-15, 26  OLED SH1106 (SPI1: dc=12, cs=13, sck=14, mosi=15, res=26)
  GPIO 27         DS18B20 one-wire (single probe)

DOOR POLARITY — the one thing to get right:
  Press the demo button, which feeds 24V into the hat's sensor JST:
      opto LED lit -> phototransistor conducts -> GP4 pulled LOW
  That is the same electrical state as the real coop's proximity switch seeing
  the closed door in front of it, so:
      GP4 LOW  = target present = DOOR CLOSED
      GP4 HIGH = pulled up by R2 = DOOR OPEN
  Nothing is inverted anywhere. Holding the button = coop shut.

Who owns state:
  This firmware does. It owns the pins, so it is the only thing that can tell
  the truth about them. Every state topic is published RETAINED, so the broker
  holds last-known values and the dashboard can render instantly on page load
  without asking anyone. On every MQTT reconnect all state is republished, which
  also covers a broker restart (Mosquitto persistence is off by default, so a
  restart drops the whole retained set).

Subscribe on your own laptop to watch the whole conversation:
  mosquitto_sub -h 192.168.4.1 -u mqtt -P mqtt -t 'demo/#' -v

Topics published:
  demo/coop_1/status          LWT: online / offline            (retained)
  demo/coop_1/reset_cause     why the board last restarted     (retained)
  demo/coop_1/switch1/state   relay 1: on / off                (retained)
  demo/coop_1/switch2/state   relay 2: on / off                (retained)
  demo/coop_1/door            open / closed                    (retained)
  demo/coop_1/temp_c          probe temperature, 1 decimal     (retained)
  demo/coop_1/wifi            JSON {rssi, quality}, every 60s
  demo/coop_1/health          JSON uptime/mem/pins, every 60s
  demo/coop_1/log             human-readable event log
  demo/coop_1/response        replies to .../request

Topics subscribed:
  demo/coop_1/switch1/set     on | off | toggle
  demo/coop_1/switch2/set     on | off | toggle
  demo/coop_1/request         ping | state | health | pins | reset

Files this needs on the Pico:
  mqtt_as.py  sh1106.py  oled_manager_large_screen_rev.py  demo_config.py
  (onewire.py and ds18x20.py ship frozen in the official Pico W build)
"""

import machine
import network
import ubinascii
import ujson
import time
import sys
import asyncio
import gc
import onewire
import ds18x20
from machine import Pin
from mqtt_as import MQTTClient, config
from oled_manager_large_screen_rev import OLEDManager
import demo_config

# ─── Identity ────────────────────────────────────────────────────────────────
# 'demo/...' and not 'jumilla/...' on purpose. The demo rig has no connection to
# the home lab, and a student reading the topic tree should not have to wonder
# whether these messages are going somewhere real.

DEVICE_ID = 'coop_1'
BASE      = f'demo/{DEVICE_ID}'
STATUS_T  = f'{BASE}/status'

# ─── Pins ────────────────────────────────────────────────────────────────────

PIN_SAFE_MODE = 2
PIN_DOOR      = 4
PIN_RELAY1    = 6
PIN_RELAY2    = 7
PIN_BUTTON2   = 8   # -> relay 2
PIN_BUTTON1   = 9   # -> relay 1
PIN_ONEWIRE   = 27

# ─── Timings ─────────────────────────────────────────────────────────────────

BUTTON_DEBOUNCE_MS = 100   # second layer; the hat's 0.1uF RC is the first
DOOR_SETTLE_MS     = 100   # a swinging door chatters at the threshold
TEMP_INTERVAL_S    = 10    # fast for a demo — a hand on the probe should show
TEMP_MEDIAN_N      = 3     # rolling median: one bad read never reaches the UI
HEALTH_INTERVAL_S  = 60

# ─── Hardware ────────────────────────────────────────────────────────────────

relay1 = Pin(PIN_RELAY1, Pin.OUT, value=0)
relay2 = Pin(PIN_RELAY2, Pin.OUT, value=0)
RELAYS = {1: relay1, 2: relay2}

# Internal pull-up as well as the hat's R2, so GP4 is still defined if R2 is
# ever unpopulated — a floating input would read as a door flapping at random.
door_pin = Pin(PIN_DOOR, Pin.IN, Pin.PULL_UP)

ds_sensor = ds18x20.DS18X20(onewire.OneWire(Pin(PIN_ONEWIRE)))
oled_mgr  = OLEDManager()

# ─── Reset cause ─────────────────────────────────────────────────────────────
# Read at module level, before any task or the WDT starts, so the reason for the
# PREVIOUS restart survives into the log and onto the splash screen. On a demo
# rig this is how you tell "someone pulled the USB" from "the watchdog fired".

_RESET_CAUSES = {v: l for v, l in (
    (getattr(machine, 'PWRON_RESET',     None), 'power-on'),
    (getattr(machine, 'WDT_RESET',       None), 'watchdog'),
    (getattr(machine, 'SOFT_RESET',      None), 'soft'),
    (getattr(machine, 'DEEPSLEEP_RESET', None), 'deepsleep'),
) if v is not None}
reset_cause = _RESET_CAUSES.get(machine.reset_cause(), f'unknown({machine.reset_cause()})')
print(f"Reset cause: {reset_cause}")

# ─── MQTT ────────────────────────────────────────────────────────────────────

config['ssid']          = demo_config.WIFI_SSID
config['wifi_pw']       = demo_config.WIFI_PASSWORD
config['server']        = demo_config.MQTT_BROKER
config['port']          = demo_config.MQTT_PORT
config['user']          = demo_config.MQTT_USER
config['password']      = demo_config.MQTT_PASSWORD
config['clean']         = True
config['client_id']     = f'demo_{DEVICE_ID}'
config['response_time'] = 30
config['queue_len']     = 1
# Last Will and Testament: the broker publishes this if we vanish without saying
# goodbye. It is what makes the dashboard's online lamp honest — the Pico cannot
# announce its own death, so the broker does it on its behalf.
config['will']          = (STATUS_T, 'offline', True, 1)

client = MQTTClient(config)

# ─── Global state ────────────────────────────────────────────────────────────

log_queue       = []
heartbeats      = {}   # subsystem name -> ticks_ms of last beat
pin_diagnostics = {}   # pin number -> counters, published on request 'pins'
door_published  = None # last door string actually sent
temp_samples    = []   # last TEMP_MEDIAN_N raw readings
temp_c          = None # last published value, None = no probe / bad reads
probe_rom       = None # DS18B20 ROM id once found

# ─── Core utilities ──────────────────────────────────────────────────────────


def beat(name):
    heartbeats[name] = time.ticks_ms()


async def safe_pub(topic, msg, qos=0, retain=False):
    try:
        await client.publish(topic, msg, qos=qos, retain=retain)
        # A qos1 publish only returns after the broker's PUBACK, so a clean
        # return proves the whole path: task running -> socket alive -> broker
        # acked. That is the liveness signal the watchdog watches. qos0 is
        # fire-and-forget and proves nothing, so it never beats.
        if qos >= 1:
            beat('mqtt')
    except Exception as e:
        # print only — appending to log_queue here would make a feedback loop
        print(f"pub err ({topic[-20:]}): {e}")


def log(msg):
    if len(log_queue) < 20:
        log_queue.append(msg)
    else:
        print(f"log full, dropped: {msg}")


async def async_logger():
    """Drains log_queue to MQTT .../log and stdout."""
    while True:
        try:
            if log_queue:
                msg = log_queue.pop(0)
                line = f"[{time.ticks_ms() // 1000}s] {msg}"
                print(line)
                await safe_pub(f'{BASE}/log', line, qos=0)
        except Exception as e:
            print(f"async_logger: {e}")
        await asyncio.sleep_ms(300)


async def supervised(name, coro_factory, restart_delay_s=2):
    """Restarts a task that dies instead of silently losing a subsystem."""
    while True:
        try:
            await coro_factory()
        except Exception as e:
            log(f"RESTART [{name}]: {e}")
            await asyncio.sleep(restart_delay_s)


async def clean_memory():
    while True:
        beat('gc')
        try:
            if gc.mem_free() < 20000:
                gc.collect()
                log(f"GC: collected, free={gc.mem_free()}")
        except Exception as e:
            log(f"clean_memory: {e}")
        await asyncio.sleep(40)


def note_event(text):
    """One line of 'what just happened', for the OLED and the log."""
    oled_mgr.set_line('line6', f'>{text}', scrolling=True)
    log(text)


def _update_relay_oled():
    r1 = 'ON ' if relay1.value() else 'OFF'
    r2 = 'ON ' if relay2.value() else 'OFF'
    oled_mgr.set_line('line3', f'R1:{r1} R2:{r2}')

# ─── Relays ──────────────────────────────────────────────────────────────────
# Active HIGH: value(1) energises the coil. If the switch hat turns out to be
# active LOW, the whole fix is to invert here and in the Pin() constructors —
# press a button on the bench and listen for the click to find out.
#
# There is no equivalent of ESPHome's restore_mode: a MicroPython board has
# nowhere to persist pin state, so both relays come up OFF after every power
# cycle. For a demo that is the behaviour you want anyway.


async def apply_relay(n, action, source):
    pin = RELAYS.get(n)
    if pin is None:
        log(f"relay{n}: no such relay")
        return
    if action == 'on':
        pin.value(1)
    elif action == 'off':
        pin.value(0)
    elif action == 'toggle':
        pin.value(not pin.value())
    else:
        log(f"relay{n}: unknown action '{action}'")
        return
    state = 'on' if pin.value() else 'off'
    await safe_pub(f'{BASE}/switch{n}/state', state, retain=True)
    _update_relay_oled()
    note_event(f'{source} r{n} {state}')

# ─── Door ────────────────────────────────────────────────────────────────────


def door_state():
    return 'closed' if door_pin.value() == 0 else 'open'


async def publish_door(source):
    """Publishes the door state, but only when it has actually changed."""
    global door_published
    state = door_state()
    if state == door_published:
        return
    door_published = state
    await safe_pub(f'{BASE}/door', state, retain=True)
    oled_mgr.set_line('line2', f'Door: {state.upper()}')
    note_event(f'{source} door {state}')

# ─── Pin watchers ────────────────────────────────────────────────────────────
# IRQ-driven, never polled. A polling loop that wedges leaves an input silently
# dead; an IRQ that stops firing takes the whole asyncio scheduler with it, and
# the watchdog catches that.


def _new_diag(pin_num, kind):
    d = {
        'type':              kind,
        'irq_fires':         0,   # total handler invocations
        'tasks_created':     0,   # times the action actually ran
        'debounce_filtered': 0,   # edges swallowed as bounce
        'last_val':         -1,
    }
    pin_diagnostics[pin_num] = d
    return d


def watch_button_irq(pin_num, action_coro, debounce_ms=BUTTON_DEBOUNCE_MS):
    """Falling edge only, fire immediately, then ignore repeats for debounce_ms.

    Fire-then-ignore, not wait-then-fire: a button should respond the instant it
    is pressed, and what needs swallowing is the release bounce afterwards. This
    is the equivalent of ESPHome's `delayed_off`, which is why the YAML uses that
    filter and not `delayed_on`.
    """
    p = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    last_trigger = [0]
    diag = _new_diag(pin_num, 'button')

    def irq_handler(pin):
        try:
            diag['irq_fires'] += 1
            diag['last_val'] = pin.value()
            if pin.value() == 1:        # released, not pressed
                return
            now = time.ticks_ms()
            if time.ticks_diff(now, last_trigger[0]) > debounce_ms:
                last_trigger[0] = now
                diag['tasks_created'] += 1
                asyncio.create_task(action_coro())
            else:
                diag['debounce_filtered'] += 1
        except Exception as e:
            log(f"IRQ pin {pin_num}: {e}")

    p.irq(trigger=Pin.IRQ_FALLING, handler=irq_handler, hard=False)


def watch_door_irq():
    """Both edges, settle, then read — ESPHome's delayed_on + delayed_off.

    A door needs both directions, and unlike a button it must NOT fire on the
    first edge: a door easing past the sensor chatters, and firing immediately
    would publish open/closed/open/closed. So the IRQ only arms a one-shot
    settle task, and that task re-reads the pin 100ms later and publishes
    whatever it actually finds. Bounce during the window costs nothing, and
    because the final value comes from reading the pin rather than from counting
    edges, a missed edge cannot leave the state inverted.
    """
    diag = _new_diag(PIN_DOOR, 'door')
    pending = [False]

    async def settle():
        try:
            await asyncio.sleep_ms(DOOR_SETTLE_MS)
            await publish_door('edge')
        except Exception as e:
            log(f"door settle: {e}")
        finally:
            pending[0] = False

    def irq_handler(pin):
        try:
            diag['irq_fires'] += 1
            diag['last_val'] = pin.value()
            if pending[0]:
                diag['debounce_filtered'] += 1
                return
            pending[0] = True
            diag['tasks_created'] += 1
            asyncio.create_task(settle())
        except Exception as e:
            log(f"IRQ door: {e}")

    door_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=irq_handler, hard=False)


async def action_button_1():
    await apply_relay(1, 'toggle', 'btn1')


async def action_button_2():
    await apply_relay(2, 'toggle', 'btn2')


def setup_pins():
    watch_button_irq(PIN_BUTTON1, action_button_1)
    watch_button_irq(PIN_BUTTON2, action_button_2)
    watch_door_irq()
    log(f"IRQ watchers registered: buttons {PIN_BUTTON1},{PIN_BUTTON2} door {PIN_DOOR}")

# ─── Temperature ─────────────────────────────────────────────────────────────
# One probe, not the weather station's two — the coop has a single DS18B20 on a
# Grove daughter board. The bus needs a 4.7k pull-up from data to 3V3; most
# breakout boards have it fitted, a bare TO-92 sensor does not, and without it
# the bus reads nothing at all.
#
# Deliberately NOT in the watchdog's critical set (see feed_the_dog). On the demo
# rig the probe is a plug-in accessory, and a board that hard-resets every 15
# minutes because nothing is plugged in is a worse teacher than one that says
# "no probe" on its screen.


def _median(vals):
    s = sorted(vals)
    return s[len(s) // 2]


async def read_temp_sensor():
    global probe_rom, temp_c
    skips = 0

    while True:
        try:
            if probe_rom is None:
                roms = ds_sensor.scan()
                if not roms:
                    oled_mgr.set_line('line4', 'Temp: no probe')
                    await asyncio.sleep(TEMP_INTERVAL_S)
                    continue
                probe_rom = roms[0]
                temp_samples.clear()
                log(f"DS18B20 found: {ubinascii.hexlify(probe_rom).decode()}")

            ds_sensor.convert_temp()
            await asyncio.sleep_ms(750)        # the chip's own conversion time
            raw = ds_sensor.read_temp(probe_rom)

            # 85.0 = the chip's power-up default, -127.0 = bus not answering.
            # Both are "no reading", not a temperature.
            if raw in (85.0, -127.0):
                raise ValueError(f"invalid reading {raw}")

            temp_samples.append(raw)
            if len(temp_samples) > TEMP_MEDIAN_N:
                temp_samples.pop(0)

            temp_c = _median(temp_samples) + demo_config.TEMP_OFFSET_C
            temp_f = (temp_c * 9 / 5) + 32
            await safe_pub(f'{BASE}/temp_c', f'{temp_c:.1f}', retain=True)
            oled_mgr.set_line('line4', f'{temp_c:.1f}C {temp_f:.1f}F')
            beat('temp')
            skips = 0

        except Exception as e:
            skips += 1
            log(f"temp skip #{skips}: {e}")
            oled_mgr.set_line('line4', f'Temp: {e}', scrolling=True)
            if skips >= 3:
                # Publishing an EMPTY payload with retain=True deletes the
                # retained message, so the dashboard shows "--" instead of a
                # stale number that looks live. Worth watching in mosquitto_sub.
                temp_c = None
                probe_rom = None
                temp_samples.clear()
                skips = 0
                await safe_pub(f'{BASE}/temp_c', '', retain=True)

        await asyncio.sleep(TEMP_INTERVAL_S)

# ─── Health publisher ────────────────────────────────────────────────────────


async def health_publisher():
    while True:
        beat('health')
        await asyncio.sleep(HEALTH_INTERVAL_S)
        try:
            now = time.ticks_ms()
            uptime_s = now // 1000
            d = uptime_s // 86400
            h = (uptime_s % 86400) // 3600
            m = (uptime_s % 3600) // 60
            blob = {
                'uptime_s':  uptime_s,
                'mem_free':  gc.mem_free(),
                'reset':     reset_cause,
                'relays':    {'r1': relay1.value(), 'r2': relay2.value()},
                'door':      door_state(),
                'temp_c':    temp_c,
                'probe':     ubinascii.hexlify(probe_rom).decode() if probe_rom else None,
                'subsystems': {
                    name: time.ticks_diff(now, ts) // 1000
                    for name, ts in heartbeats.items()
                },
                'pins': {str(k): v for k, v in pin_diagnostics.items()},
            }
            await safe_pub(f'{BASE}/health', ujson.dumps(blob), qos=1)
            oled_mgr.set_line('line7', f'Up:{d}d {h:02d}h {m:02d}m')
            oled_mgr.set_line('line8', f'Mem:{gc.mem_free() // 1024}k')

            # Reconciliation. The door topic is an event stream, and an event
            # stream with no reconciliation drifts the first time an edge is
            # missed. This re-reads the actual pin once a minute and publishes
            # only on disagreement, so a lost edge self-heals within 60s instead
            # of leaving a wrong state on screen until the door next moves.
            await publish_door('sync')
        except Exception as e:
            log(f"health_publisher: {e}")

# ─── WiFi monitor ────────────────────────────────────────────────────────────


async def wifi_monitor():
    sta_if = network.WLAN(network.STA_IF)
    while True:
        beat('wifi')
        try:
            if sta_if.isconnected():
                rssi = sta_if.status('rssi')
                quality = ("great" if rssi >= -50 else
                           "good"  if rssi >= -70 else
                           "fair"  if rssi >= -80 else "poor")
                await safe_pub(f'{BASE}/wifi',
                               ujson.dumps({'rssi': rssi, 'quality': quality}),
                               qos=1)
                oled_mgr.set_line('line5', f'WiFi:{quality}({rssi})')
            else:
                log("WiFi: disconnected")
                oled_mgr.set_line('line5', 'WiFi: down')
        except Exception as e:
            log(f"wifi_monitor: {e}")
        await asyncio.sleep(60)

# ─── Watchdog ────────────────────────────────────────────────────────────────


async def feed_the_dog(wd):
    """Feeds the hardware WDT only while every critical subsystem is checking in.

    Two subsystems are deliberately absent from the critical set, and both
    omissions are specific to a demo rig:

      'temp' — the probe is a plug-in accessory here (see read_temp_sensor).
      'mqtt' — the home-lab firmware demands a qos1 PUBACK every 180s, which
               self-heals the "socket up, LWT says online, publishing wedged"
               failure. But on this rig the broker is the thing being taught,
               and it WILL be stopped, restarted and reconfigured mid-session.
               With 'mqtt' critical, every one of those restarts reboot-loops
               the Pico every three minutes. mqtt_as reconnects on its own, and
               for the rare genuine wedge there is the 'reset' request command
               and a USB cable. safe_pub still beats 'mqtt' and it still shows
               up in .../health — it is informational here, not a trigger.

    What is left guards the one thing nothing else can recover from: a frozen
    asyncio scheduler, where these tasks stop running at all.

    Ground GPIO 2 to disable all of this for bench work.
    """
    critical = {
        'wifi':   120_000,
        'health': 120_000,
        'gc':     120_000,
    }
    while True:
        now = time.ticks_ms()
        stale = [
            name for name, max_ms in critical.items()
            if name not in heartbeats or time.ticks_diff(now, heartbeats[name]) >= max_ms
        ]
        if stale:
            log(f"WDT: stale {stale} -- reset imminent")
        else:
            wd.feed()
        await asyncio.sleep(3)

# ─── MQTT handlers ───────────────────────────────────────────────────────────


async def mqtt_action_sw1(topic_str, msg_str):
    await apply_relay(1, msg_str, 'mqtt')


async def mqtt_action_sw2(topic_str, msg_str):
    await apply_relay(2, msg_str, 'mqtt')


async def publish_all_state():
    """Republishes every retained state topic from the real hardware.

    Two jobs. On reconnect it restores the retained set, which a Mosquitto
    restart would otherwise have dropped (persistence is off by default). And on
    request it overwrites anything a person published by hand — the broker will
    happily retain a fake relay state, and this is the only thing that can put
    the truth back, because only this board can read the pins.
    """
    global door_published
    for n, pin in RELAYS.items():
        await safe_pub(f'{BASE}/switch{n}/state', 'on' if pin.value() else 'off', retain=True)
    door_published = None          # force publish_door to send regardless
    await publish_door('resync')
    await safe_pub(f'{BASE}/temp_c',
                   f'{temp_c:.1f}' if temp_c is not None else '', retain=True)
    await safe_pub(f'{BASE}/reset_cause', reset_cause, retain=True)


async def mqtt_action_request(topic_str, msg_str):
    if msg_str == 'ping':
        await safe_pub(f'{BASE}/response', 'pong', qos=0)

    elif msg_str == 'state':
        await publish_all_state()
        await safe_pub(f'{BASE}/response', 'state republished', qos=0)

    elif msg_str == 'pins':
        gc.collect()
        await safe_pub(f'{BASE}/pins',
                       ujson.dumps({str(k): v for k, v in pin_diagnostics.items()}), qos=0)

    elif msg_str == 'health':
        gc.collect()
        now = time.ticks_ms()
        blob = {
            'uptime_s': now // 1000,
            'mem_free': gc.mem_free(),
            'reset':    reset_cause,
            'relays':   {'r1': relay1.value(), 'r2': relay2.value()},
            'door':     door_state(),
            'temp_c':   temp_c,
            'subsystems': {
                name: time.ticks_diff(now, ts) // 1000
                for name, ts in heartbeats.items()
            },
        }
        await safe_pub(f'{BASE}/health', ujson.dumps(blob), qos=0)

    elif msg_str == 'reset':
        log('reset requested via MQTT')
        await asyncio.sleep_ms(200)      # let the log line reach the broker
        machine.reset()

    else:
        log(f"unknown request: {msg_str}")


mqtt_map = {
    f'{BASE}/switch1/set': mqtt_action_sw1,
    f'{BASE}/switch2/set': mqtt_action_sw2,
    f'{BASE}/request':     mqtt_action_request,
}

# ─── MQTT connect + event tasks ──────────────────────────────────────────────


async def mqtt_connect_with_retry():
    attempts = 0
    while True:
        try:
            attempts += 1
            if attempts > 5:
                print("MQTT: max retries exceeded, resetting")
                await asyncio.sleep(2)
                machine.reset()
            print(f"MQTT connect attempt {attempts}")
            oled_mgr.set_line('line5', f'MQTT try {attempts}')
            await asyncio.sleep(1)
            await client.connect()
            print("MQTT connected")
            return
        except OSError as e:
            print(f"MQTT conn err #{attempts}: {e}")
            await asyncio.sleep(10)


async def up(client):
    """Runs on every (re)connect, including the first."""
    while True:
        try:
            await client.up.wait()
            client.up.clear()
            await asyncio.sleep(0.5)
            for topic in mqtt_map:
                await client.subscribe(topic, 1)
            await safe_pub(STATUS_T, 'online', retain=True, qos=0)
            await publish_all_state()
            beat('mqtt_up')
            beat('mqtt')    # seed the liveness beat: a fresh connect grants the
                            # full 180s grace before qos1 acks take over
            log("MQTT up, subscribed, state republished")
        except Exception as e:
            log(f"up(): {e}")


async def _run_action(func, topic, msg):
    try:
        await func(topic, msg)
    except Exception as e:
        log(f"mqtt action [{topic}]: {e}")


async def messages(client):
    while True:
        try:
            async for topic, msg, retained in client.queue:
                t = topic.decode()
                m = msg.decode()
                if t in mqtt_map:
                    asyncio.create_task(_run_action(mqtt_map[t], t, m))
                else:
                    log(f"unknown topic: {t}")
        except Exception as e:
            log(f"messages(): {e}")
            await asyncio.sleep(2)

# ─── Main ────────────────────────────────────────────────────────────────────


async def main():
    global probe_rom

    safe_mode_pin = Pin(PIN_SAFE_MODE, Pin.IN, Pin.PULL_UP)
    await asyncio.sleep_ms(50)
    wdt_enabled = (safe_mode_pin.value() == 1)

    # Scan the bus before the splash so the splash can report it. A wrong
    # one-wire pin or a missing 4.7k pull-up reads as "no probe" with no error
    # anywhere, and two seconds of 'DS:NO' on boot turns that into a visible
    # fact instead of a mystery.
    try:
        roms = ds_sensor.scan()
        probe_rom = roms[0] if roms else None
    except Exception as e:
        print(f"bus scan: {e}")
        probe_rom = None

    await oled_mgr.show_splash(
        'Coop Demo',
        f'Rst:{reset_cause}',
        f"{'WDT ON' if wdt_enabled else 'SAFE'} DS:{'yes' if probe_rom else 'NO'}",
        delay=2,
    )

    oled_mgr.set_line('line1', 'Coop Demo')
    oled_mgr.set_line('line2', f'Door: {door_state().upper()}')
    _update_relay_oled()
    oled_mgr.set_line('line4', 'Temp: --' if probe_rom is None else 'Temp: wait')
    oled_mgr.set_line('line5', 'WiFi: connecting')
    asyncio.create_task(oled_mgr.start())

    print(f"Watchdog: {'ENABLED' if wdt_enabled else 'SAFE MODE (GPIO2 grounded)'}")
    print(f"DS18B20: {ubinascii.hexlify(probe_rom).decode() if probe_rom else 'not found'}")

    await mqtt_connect_with_retry()

    asyncio.create_task(async_logger())
    log(f"Boot: reset={reset_cause} wdt={'on' if wdt_enabled else 'off'}")
    asyncio.create_task(up(client))
    asyncio.create_task(messages(client))
    asyncio.create_task(supervised('temp',   read_temp_sensor))
    asyncio.create_task(supervised('health', health_publisher))
    asyncio.create_task(supervised('wifi',   wifi_monitor))
    asyncio.create_task(supervised('gc',     clean_memory))

    if wdt_enabled:
        # Seed every critical beat BEFORE arming, so each subsystem gets its full
        # threshold window from boot. Without this, a beat that is simply "not
        # there yet" counts as stale and the 8s hardware WDT fires long before
        # the intended allowances ever apply.
        for name in ('wifi', 'health', 'gc'):
            beat(name)
        wdt = machine.WDT(timeout=8000)
        asyncio.create_task(feed_the_dog(wdt))

    setup_pins()
    await publish_door('boot')

    while True:
        await asyncio.sleep(60)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
except Exception as e:
    print(f"Exception {e}: {type(e).__name__}")
    sys.print_exception(e)
    machine.reset()
