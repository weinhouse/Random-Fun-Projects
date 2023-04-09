## My solution to restrictive Proxmox policy

I was looking for a solution to host a couple virtual machines on my home network. I've settled on mini computers to do this, first being an "Intel NUC" and currently working on setting up a second "Lenovo M710q". The goal is to create images that use a database and local storage that syncronizes to a Dropbox account that I have. This way I can have one VM server and one backup which can easily move to if the first hardware fails.:
- Two main servers
  - VM-1: to use for general monitoring and utilities for network, also housing two docker images
    - docker image for application server running web service, cgi service, django framework, etc.
    - docker image for database server (mysql)
  - VM-2 to use as a home assistant server for my home automation experimentation and use.

### Here is my Lenovo install notes if they can help:
<details>

##### Drivers:
  I was able to pick up drivers from kernel.org:
  
`https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/snapshot/linux-firmware-main.tar.gz`

wifi drivers or disable in bios
iwlwifi-8265-34.ucode, iwlwifi-8265-36.ucode
when asked for while installing type ALT+F3 for a new terminal, mount a usb and copy files to /lib/firmware
back to ALT+F1 to go back to installation and you should be good, may need to fiddle a bit if you have different hardware.


bluetooth firmware AltF3 terminal after install, create directory /usr/lib/firmware/intel/
don't really need for my headless setup, you may want a GUI and if so, I belive driver files will be copied?? but. . .
ibt-12-16.sfi and ibt-12-16.ddc files
enable bluetooth with systemctl enable bluetooth (may still get error, but should fix)

</details>

### Once setisfied with the server install:
I'm using debian 11 which does not have sudo, so need to install it and then add user to it **(su - to become root)**
- Add LVM:
  - `apt install --no-install-recommends qemu-system libvirt-clients libvirt-daemon-system`
- Add image stuff:
  - `apt install qemu qemu-utils qemu-system-x86 virtinst`
- Add some additional stuff (you may need additional depending on your needs):
  - `apt install netcat dnsmasq bridge-utils sudo`
- home assistant needs UEFI BIOS:
  - `apt install ovmf`
- edit sutoers file with <username from install> ALL=(ALL:ALL) NOPASSWD:ALL
  
## More to come :-)
