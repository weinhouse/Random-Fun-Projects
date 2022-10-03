##### Set up pi zero w:
```
Image = 2022-04-04-raspios-bullseye-armhf-lite.img

Burn Image and gadget mode.
https://github.com/weinhouse/home/blob/master/pi/gadget_mode.md
Was a change and we are unable to log in gadget mode as pi user:
 - add authorized_keys file to pi user on the root file system of sd card.

Log in gadged mode:

add user larryw `adduser larryw`
   - copy authorized_keys from pi user to larryw user
   - add larryw to /etc/sudoers.d/010_pi-nopasswd

add wireless access /etc/wpa_supplicant/wpa_supplicant.config
network={
	ssid="Shed"
	psk=""
}


apt update
apt upgrade

Set time zone.


Install wiring pi -
install git apt install git
git clone https://github.com/WiringPi/WiringPi.git
cd WiringPi && .build

Install pip
apt install python3-pip

compile vim
https://github.com/weinhouse/notes/blob/master/vim.md

apt install jq
```
