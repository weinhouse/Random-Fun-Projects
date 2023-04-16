## Server to host virutal machines, my solution to a restrictive Proxmox policy

I was looking for a solution to host a couple virtual machines on my home network. After some research, I was planning to use Proxmox. The problem was that there is a restrictive policy where non paying users have to use a repo that Proxmox will not stand behind. Statements like "mostly stable, but not fully tested versions" and others like "do not use for production" helped me to change my mind. I decided to use good old Debian(11) with built in [KVM](https://wiki.debian.org/KVM#Introduction), libvert, and some utilities like [virt-manager](https://virt-manager.org/), and virt-install. Seems to run well on mini computers, first being my existing "Intel NUC", and currently I'm setting up a second "Lenovo M710q". The goal is to create virtual machines that will use my current docker images for applications and database storage plus local storage which syncronizes to Dropbox cloud storage. This way I can have one machine for my virtual machines, and one as a warm/hot backup.:

- Virtual machines to replace currently running hardware machines:
  - VM-1: to use for general monitoring and utilities for my network, also house my two docker images
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
- Add some additional stuff (possibly more depending on your needs):
  - `apt install netcat dnsmasq bridge-utils sudo`
- home assistant needs UEFI BIOS:
  - `apt install ovmf`
- edit sutoers file with `<username from install>` ALL=(ALL:ALL) NOPASSWD:ALL
- add public key to your virtual server for logging in and using virt-manager from a workstation to virtual server:
  - `/home/`<username from install>`/.ssh/authorized_keys`
- add `<user from install>` to libvirt group:
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
virt-install --name jumilla-virt \
--description "Server to host my docker images" \
--os-variant=generic \
--ram=4096 \
--disk size=120
--vcpus=2 \
--network bridge=br0 \
--location ./debian-11.6.0-amd64-netinst.iso \
--disk path=./jumilla-virt.qcow2,size=10 \
--graphics none \
--console pty,target_type=serial \
--extra-args "console=ttyS0"
```
`CTL + 5 gets you out of the shell`
- Home assistant install:
```
virt-install --name hass-jumilla \
--description "Home Assistant OS" \
--os-variant=generic \
--ram=2048 \
--vcpus=2 \
--disk ./haos_ova-9.5.qcow2,bus=sata \
--graphics none \
--boot uefi
```
`CTL + 5 gets you out of the shell`
