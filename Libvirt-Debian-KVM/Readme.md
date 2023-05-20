## Hardware hosting virutal machines

I was looking for a solution to host a couple virtual machines on my home network. After some research, I was planning to use Proxmox. The problem was that there is a restrictive policy where non paying users have to use a repo that Proxmox will not stand behind. Statements like "mostly stable, but not fully tested versions" and others like "do not use for production" helped me to change my mind. I decided to use good old Debian(11) with built in [KVM](https://wiki.debian.org/KVM#Introduction), libvert, and some utilities like [virt-manager](https://virt-manager.org/), and virt-install. Seems to run well on mini computers, first being my existing "Intel NUC", and currently I'm setting up a second "Lenovo M710q". The goal is to create virtual machines that will use my current docker images for applications and database storage plus local storage which syncronizes to Dropbox cloud storage. This way I can have one machine for my virtual machines, and one machine as a warm/hot backup.:

- Virtual machines to replace currently running hardware machines:
  - VM-1: to use for general monitoring and utilities for my network, also house a few docker images for Web Server, DB Server, Apps etc.
  - VM-2 to use as a home assistant server for my home automation experimentation and use.

### I do a very basic install (Lenovo M710q), your install may be different:
- Single partition entire disk
- I remove desktop software and install ssh server
- Although I'm not using in my headless server I picked up and copied to /lib/firmware files from [git.kernel.org](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/)
  - wifi drivers: iwlwifi-8265-34.ucode, iwlwifi-8265-36.ucode, and copy files to /lib/firmware
  - bluetooth firmware: ibt-12-16.sfi and ibt-12-16.ddc files
    - enable bluetooth with systemctl enable bluetooth (may still get error, but should fix)

### Once satisfied with the server install I configured with the following:
**I'm using debian 11 which does not have sudo, so need to install it and then add user to it (su - to become root)**
- KVM stuff:
  - `apt install --no-install-recommends qemu-system libvirt-clients libvirt-daemon-system`
- Add image stuff:
  - `apt install qemu qemu-utils qemu-system-x86 virtinst`
- Add some additional stuff (possibly more depending on your needs):
  - `apt install netcat dnsmasq bridge-utils sudo`
- home assistant needs UEFI BIOS:
  - `apt install ovmf`
- edit /etc/sudoers file with `<username from install> ALL=(ALL:ALL) NOPASSWD:ALL`
- add public key to your virtual server for logging in and using virt-manager from a workstation to virtual server:
  - add in ~/.ssh/authorized_keys
- first time I ssh to server I get ".Xauthority does not exist" error message, fixed with `touch ~/.Xauthority`
- add the user you added when installing to libvirt group:
  - `adduser <user name from install> libvirt`
- start and set up auto start networking:
  - `virsh --connect=qemu:///system net-start default`
  - `virsh --connect=qemu:///system net-autostart default`
- Bridge configuration /etc/network/interfaces **edit for your network environment**
```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
# allow-hotplug enp0s31f6
# iface enp0s31f6 inet dhcp

#make sure we don't get addresses on our raw device
iface enp0s31f6 inet manual
iface enp0s31f6 inet6 manual

#set up bridge and give it a static ip
auto br0
iface br0 inet static
        address 192.168.1.37
        netmask 255.255.255.0
        network 192.168.1.0
        broadcast 192.168.1.255
        gateway 192.168.1.1
        bridge_ports enp0s31f6
        bridge_stp off
        bridge_fd 0
        bridge_maxwait 0
        dns-nameservers 192.168.1.1 8.8.8.8

#allow autoconf for ipv6
iface br0 inet6 auto
        accept_ra 1
```

- Should now be able to run virt-manager on your workstation and attach to your virtual host server to install instance or I like to use vert-install
- **on `<virtual machine server>`: `cd /var/lib/libvert/images` need to have iso or .qcow2 files in this directory for installs**
  
- install a regular debian instance
 ```
virt-install --name weinvirt \
--description "weinhouse jumilla network server" \
--os-variant=generic \
--ram=8192 \
--vcpus=2 \
--network bridge=br0 \
--location ./debian-11.6.0-amd64-netinst.iso \
--disk path=./weinvirt.qcow2,size=60 \
--graphics none \
--console pty,target_type=serial \
--extra-args "console=ttyS0"
```
`CTL + 5 gets you out of the shell`

- Home assistant install:
```
Home assistant install:
virt-install --name hass-jumilla \
--description "Home Assistant OS" \
--os-variant=generic \
--ram=2048 \
--vcpus=2 \
--disk ./haos_ova-10.1.qcow2,bus=sata \
--graphics none \
--boot uefi \
--hostdev 001-013
```
