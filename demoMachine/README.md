# Pi4 IoT Dashboard

A Raspberry Pi 4B configured as a self-contained IoT demo device. The Pi4 acts as a WiFi hotspot, runs a Mosquitto MQTT broker, and serves a real-time Flask web dashboard. IoT devices (Pico W microcontrollers) connect to the hotspot, communicate via MQTT, and are monitored and controlled through the web dashboard.


# Operational Behavior
- **With ethernet:** pi gets internet access: you can ssh via 192.168.1.5 (this is your network)
- **Standalone (No Ethernet):** eth0 will show as `unavailable` or `disconnected`. You can still ssh via the wi-fi at 192.168.4.1
- **Client Connections:** Android devices will warn "No Internet" This is correct. The local network is active, and the device will communicate in the 192.168.4.x network.

## Image the pi4 using Raspberry pi imager:
***
### After the following I created a [backup image](https://www.dropbox.com/scl/fi/g0w18qcrupod8lokd74e4/demoMachinePi4B_piShrink.img.gz?rlkey=il7a8pncgrepvf54p8jayqxoj&st=2dgxhzp0&dl=0) of the sd card for quick recovery if it becomes corrupted saved In Dropbox
- Use Raspberry Pi imager to create the image
- Image will be the size of the sd card (32GB in this case)
- Reduce the size of this image with PiShrink script and gzip the file becomes ~2GB
- Use Raspberry Pi imager to place this backup image on new sd card
- Check root partition, may be the 2GB size, use raspi-config on the pi4 to extend this partition to full size.

## Create the Netplan config:
```
# Remove any existing/empty configs
sudo rm /etc/netplan/*.yaml

# Create the master renderer file
echo -e "network:\n  version: 2\n  renderer: NetworkManager" | sudo tee /etc/netplan/01-network-manager-all.yaml

# Apply the change
sudo netplan apply
```
## Configure the Hotspot 
**Get this working before you edit eth0 so your not completely locked out**
```
# 1. Create the profile
sudo nmcli con add type wifi con-name onboard-hotspot ifname wlan0 autoconnect yes ssid demomachine

# 2. Set to Access Point mode (2.4GHz)
sudo nmcli con modify onboard-hotspot 802-11-wireless.mode ap 802-11-wireless.band bg

# 3. Set Security (WPA2)
sudo nmcli con modify onboard-hotspot wifi-sec.key-mgmt wpa-psk wifi-sec.psk 818pierce

# 4. Set Static IP and DHCP Range (192.168.4.2 to 192.168.4.51)
sudo nmcli con modify onboard-hotspot ipv4.method shared ipv4.addresses 192.168.4.1/24
sudo nmcli con modify onboard-hotspot ipv4.shared-dhcp-range "192.168.4.2,192.168.4.51"

# 5. Optimization (Disable IPv6 to prevent hangs)
sudo nmcli con modify onboard-hotspot ipv6.method ignore

# 6. Activation
sudo nmcli con up onboard-hotspot
```
### Edits to HotSpot to help picoW connect
```
# Force WPA2 (RSN) and disable WPA3/PMF requirements
sudo nmcli connection modify "onboard-hotspot" 802-11-wireless-security.proto rsn
sudo nmcli connection modify "onboard-hotspot" 802-11-wireless-security.group ccmp
sudo nmcli connection modify "onboard-hotspot" 802-11-wireless-security.pairwise ccmp
sudo nmcli connection modify "onboard-hotspot" 802-11-wireless-security.pmf 1

# Restart the connection to apply changes
sudo nmcli connection down "onboard-hotspot"
sudo nmcli connection up "onboard-hotspot"
```

## Static Ethernet Assignment (confirm that it's name is eth0)
```
# Create a permanent profile for the Ethernet port
sudo nmcli con add type ethernet con-name eth0 ifname eth0 \
  ipv4.method manual \
  ipv4.addresses 192.168.1.5/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8,1.1.1.1" \
  connection.autoconnect yes

# Apply the profile
sudo nmcli con up eth0
```

## Optional, remove IP v6
```
sudo vi /boot/firmware/cmdline.txt
# at end of file place:
ipv6.disable=1
```
### System-wide config to remove ipv6
```
sudo tee -a /etc/sysctl.conf <<EOF
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
net.ipv6.conf.eth0.disable_ipv6 = 1
net.ipv6.conf.wlan0.disable_ipv6 = 1
EOF

sudo sysctl -p
```
**edit** `/etc/NetworkManager/system-connections/eth0.nmconnection`
```
[ipv6]
method=ignore
```
## Reload and restart
```
sudo nmcli connection reload
sudo nmcli con up eth0
```

## Demo dashboard to see who logs in
```
watch -n 1 "awk '{print \$3, \"\t\", \$4}' /var/lib/NetworkManager/dnsmasq-wlan0.leases"
```
## Troubleshooting commands
```
nmcli device
ip addr show wlan0
sudo iw dev wlan0 station dump
sudo journalctl -u NetworkManager -f
sudo nmcli radio wifi off && sudo nmcli radio wifi on
```

## 2. Installation: Nginx & Mosquitto

Run these commands on your Pi to install the core components:

```bash
# Update and install
sudo apt update
sudo apt install -y nginx mosquitto mosquitto-clients python3-flask python3-gunicorn

# Enable Mosquitto to start on boot
sudo systemctl enable mosquitto

```

---

## 3. Configuring Mosquitto for the Pico W

By default, modern Mosquitto versions only allow connections from the local machine. To allow your Pico W to connect, we must open it to the network.

**Edit the config:**

```bash
sudo nano /etc/mosquitto/conf.d/local.conf

```

**Add these lines:**

```# Listen on the standard port for all interfaces
listener 1883 0.0.0.0

# Allow connections without a username/password (typical for local demos)
allow_anonymous false
password_file /etc/mosquitto/passwd

```

Password: `mosquitto_passwd -c /etc/mosquitto/passwd mqtt

**Restart Mosquitto:**

```bash
sudo systemctl restart mosquitto

```

---

**The flask app** `app.pi`

**Create the directory:**

```bash
mkdir ~/demo_app && cd ~/demo_app

```

## Connecting Flask to Nginx

To make this professional, we tell Nginx to "pass" traffic from port 80 (standard web) to your Flask app.

**Edit the Nginx default site:**

```bash
sudo nano /etc/nginx/sites-available/default

```

**Find the `location /` block and change it to:**

```text
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

```

**Restart Nginx:**

```bash
sudo systemctl restart nginx

```

## Systemd to start the app:
`sudo vi /etc/systemd/system/demomachine.service`

```
[Unit]
Description=Gunicorn instance to serve Demomachine UI
# Wait for the network and Mosquitto to be ready before starting
After=network.target mosquitto.service

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/demo_app
# Use the python/gunicorn inside your virtual environment
Environment="PATH=/home/pi/demo_app/venv/bin"
ExecStart=/home/pi/demo_app/venv/bin/gunicorn --threads 4 --bind 127.0.0.1:5000 app:app

# Automatically restart the app if it crashes
Restart=always

[Install]
WantedBy=multi-user.target
```
Now, tell the system to recognize the new file and start it up:
```
# Reload the system to see the new file
sudo systemctl daemon-reload

# Enable it to start on boot
sudo systemctl enable demomachine

# Start it now
sudo systemctl start demomachine
```
**Check status** `sudo systemctl status demomachine`
**See live logs:** `journalctl -u demomachine.service -f`

