 #!/bin/sh


#set static ip
sudo ifconfig eth0 192.168.50.1 netmask 255.255.255.0 up
sudo route add default gw 192.168.50.1
#sudo ip route add default via 192.168.50.1 dev eth0
sudo ifconfig eth0 down
sudo ifconfig eth0 up



# set iptable forward
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -F
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE 
