 #!/bin/sh

#make ram disk
if [ ! -d "/tmp/ramdisk" ] 
then
    sudo mkdir /tmp/ramdisk
	sudo chmod 777 /tmp/ramdisk
	sudo mount -t tmpfs -o size=1024m myramdisk /tmp/ramdisk
	# nano /etc/fstab
	#myramdisk  /tmp/ramdisk  tmpfs  defaults,size=1G,x-gvfs-show  0  0
	echo "myramdisk  /tmp/ramdisk  tmpfs  defaults,size=1G,x-gvfs-show  0  0" | sudo tee -a /etc/fstab
	echo "" | sudo tee -a /etc/fstab
	sudo mount -a

fi

sudo apt-get update && sudo apt-get upgrade
sudo apt -y install xscreensaver
pip3 install paramiko
sudo apt-get -y install qt5-default pyqt5-dev pyqt5-dev-tools
#sudo apt-get -y install matchbox-keyboard
sudo apt -y install python3-opencv python3-opencv-apps
sudo apt-get -y install libatlas-base-dev



#auto remove no use
sudo apt-get -y remove python-pygame
sudo apt-get -y remove minecraft-pi
sudo apt -y autoremove
sudo apt-get -y purge wolfram-engine
sudo apt-get -y purge libreoffice*
sudo apt-get -y clean
sudo apt-get -y autoremove

##uponly
sudo apt-get install libfakekey-dev libpng-dev libxft-dev autoconf libtool -y
cd /tmp/ramdisk
git clone https://github.com/xlab/matchbox-keyboard.git
cd matchbox-keyboard
./autogen.sh
make
sudo make install
cd ~/Desktop/pyUI


##end uponly

#### downonly
pip3 install scikit-image
pip3 install scipy
##end downonly



#https://blog.csdn.net/qq1187239259/article/details/80022272
#setting up raspi share network
#sudo sysctl -w net.ipv4.ip_forward=1
#sudo ifconfig eth0 169.254.107.211 netmask 255.255.0.0 up
#sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
#sudo iptables -I FORWARD -o eth0 -s 169.254.107.211/16 -j ACCEPT
#sudo iptables -I INPUT -s 169.254.107.211/16 -j ACCEPT
