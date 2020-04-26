 #!/bin/sh

#set static ip
sudo ifconfig eth0 192.168.50.10 netmask 255.255.255.0 up
if grep "192.168.50.1" /etc/resolv.conf
then
    # code if found
else
    echo "nameserver 192.168.50.1" | sudo tee -a /etc/resolv.conf
fi
sudo route add default gw 192.168.50.1
#sudo ip route add default via 192.168.50.1 dev eth0
sudo ifconfig eth0 down
sudo ifconfig eth0 up

