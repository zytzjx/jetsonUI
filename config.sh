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
sudo apt-get -y purge libreoffice*
sudo apt-get -y clean
sudo apt-get -y autoremove

sudo apt-get -y install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev liblapack-dev libblas-dev gfortran

sudo apt-get -y install qt5-default pyqt5-dev pyqt5-dev-tools
sudo apt-get -y install python3-matplotlib python3-numpy python3-pil python3-scipy python3-tk
sudo apt-get -y install build-essential python3-dev cython3 python3-setuptools python3-pip python3-wheel python3-numpy python3-pytest python3-blosc python3-brotli python3-snappy python3-lz4 libz-dev libblosc-dev liblzma-dev liblz4-dev libzstd-dev libpng-dev libwebp-dev libbz2-dev libopenjp2-7-dev libjpeg-turbo8-dev libjxr-dev liblcms2-dev libcharls-dev libaec-dev libbrotli-dev libsnappy-dev libzopfli-dev libgif-dev libtiff-dev


wget https://bootstrap.pypa.io/get-pip.py 
python3 ./get-pip.py
rm ./get-pip.py

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow
python3 -m pip install --upgrade pyserial
python3 -m pip install imagecodecs==2019.5.22
python3 -m pip install scikit-image==0.16.2
python3 -m pip install dataclasses


##low is zero
sudo apt-get update
sudo apt-get install avahi-daemon avahi-discover libnss-mdns

##uponly
sudo apt-get install libfakekey-dev libpng-dev libxft-dev autoconf libtool -y
cd /tmp/ramdisk
git clone https://github.com/xlab/matchbox-keyboard.git
cd matchbox-keyboard
./autogen.sh
make
sudo make install
cd ~/Desktop/jetsonUI
cp ./PSI.desktop ~/Desktop/


##end uponly

#https://blog.csdn.net/qq1187239259/article/details/80022272
#setting up raspi share network
#sudo sysctl -w net.ipv4.ip_forward=1
#sudo ifconfig eth0 169.254.107.211 netmask 255.255.0.0 up
#sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
#sudo iptables -I FORWARD -o eth0 -s 169.254.107.211/16 -j ACCEPT
#sudo iptables -I INPUT -s 169.254.107.211/16 -j ACCEPT
