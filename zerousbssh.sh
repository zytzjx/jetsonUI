#cp ./zerousbssh.sh /etc/profile.d/zerousbssh.sh
sudo  avahi-autoipd -D usb0
sudo ifconfig usb0:avahi 192.168.7.1 netmask 255.255.255.0 up
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

