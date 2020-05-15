Install PyQT5

sudo apt-get update
sudo apt-get install qt5-default pyqt5-dev pyqt5-dev-tools

autorun:https://blog.csdn.net/geyo1992/article/details/80049821
sudo nano /etc/rc.local

export DISPLAY=:0
#X -nocursor -s 0 -dpms &
/home/pi/Desktop/pyUI/start.sh &

sudo nano ~/.config/lxsession/LXDE-pi/autostart
@lxpanel --profile LXDE
@pcmanfm --desktop --profile LXDE
@xscreensaver -no-splash
@/home/pi/Desktop/pyUI/start.sh




sudo apt install python3-opencv


Install virtual keyboard
Step1: Execute the following commands to install the corresponding software
sudo apt-get update

sudo apt-get install matchbox-keyboard

sudo nano /usr/bin/toggle-matchbox-keyboard.sh

Step2: Copy the following contents to toggle box - keyboard. Sh, save the exit
#!/bin/bash
#This script toggle the virtual keyboard
PID=pidof matchbox-keyboard
if [ ! -e $PID ]; then
killall matchbox-keyboard
else
matchbox-keyboard -s 50 extended&
fi
Step3: Execute the following command
sudo chmod +x /usr/bin/toggle-matchbox-keyboard.sh

sudo mkdir /usr/local/share/applications

sudo nano /usr/local/share/applications/toggle-matchbox-keyboard.desktop

Step4: Copy the following contents to toggle - matchbox - keyboard. Desktop, save exit
[Desktop Entry]
Name=Toggle Matchbox Keyboard
Comment=Toggle Matchbox Keyboard`
Exec=toggle-matchbox-keyboard.sh
Type=Application
Icon=matchbox-keyboard.png
Categories=Panel;Utility;MB
X-MB-INPUT-MECHANSIM=True
Step5: To perform the following command, note that this step must use the "PI" user permission, and if the administrator privileges are used, the file will not be found
nano ~/.config/lxpanel/LXDE-pi/panels/panel

Step6: Find similar commands (different versions of ICONS may differ)
Plugin {
type = launchbar
Config {
Button {
id=lxde-screenlock.desktop
}
Button {
id=lxde-logout.desktop
}
}
Step7: Add the following code to add a Button item
Button {
id=/usr/local/share/applications/toggle-matchbox-keyboard.desktop
}
Step8: To restart the system with the following command, you can see a virtual keyboard icon in the top left corner
sudo reboot

Create a RAM Disk
sudo mkdir /tmp/ramdisk
sudo chmod 777 /tmp/ramdisk
sudo mount -t tmpfs -o size=1024m myramdisk /tmp/ramdisk
sudo nano /etc/fstab
myramdisk  /tmp/ramdisk  tmpfs  defaults,size=1G,x-gvfs-show  0  0
sudo mount -a

sudo apt install xscreensaver

#pip install pyserial                 #system has installed
#pip3 install pyserial

#pip install mprpc
#pip3 install mprpc

#pip3 install gsocketpool

#pip3 install scp
pip3 install paramiko

pip3 install scikit-image
pip3 install scipy

#how to compile matchbox-keyboard
#https://ozzmaker.com/virtual-keyboard-for-the-raspberry-pi/
sudo apt-get install libfakekey-dev libpng-dev libxft-dev autoconf libtool -y
git clone https://github.com/xlab/matchbox-keyboard.git
cd matchbox-keyboard
./autogen.sh
make
sudo make install

 #sudo apt-get install libmatchbox1 -y
 
#passwordless
ssh-keygen -t rsa
ssh pi@192.168.1.30 mkdir -p .ssh
cat ~/.ssh/id_rsa.pub | ssh pi@192.168.1.30 'cat >> .ssh/authorized_keys'
ssh pi@192.168.1.30 "chmod 700 .ssh; chmod 640 .ssh/authorized_keys"
ssh pi@192.168.1.30

rsync -avzP --delete pi@192.168.1.12:/home/pi/Desktop/pyUI/profiles/ /home/pi/Desktop/pyui/profiles/

#no password login ssh settings and rsync
ssh-keygen
#all response enter [Press enter key]
ssh-copy-id -i ~/.ssh/id_rsa.pub remote-host
ssh remote-host

#使用sed命令删除\r字符
sed -i 's/\r//g' /etc/network/interfaces 

#/etc/network/interfaces
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet static

address 169.254.115.191
gateway 169.254.107.211
netmask 255.255.0.0
network 169.254.0.0
broadcast 169.254.255.255



#take picture settings
cd /tmp
wget https://project-downloads.drogon.net/wiringpi-latest.deb
sudo dpkg -i wiringpi-latest.deb


#Ubuntu access tty deny
sudo usermod -a -G tty qa
sudo chown qa /dev/ttyUSB0


https://learn.adafruit.com/turning-your-raspberry-pi-zero-into-a-usb-gadget/ethernet-gadget
https://idea.isnew.info/how-to-connect-to-the-internet-over-usb-from-the-raspberry-pi-zero.html

https://ubuntu1804.blogspot.com/2019/08/jetson-nano-python3-install-scikit-image.html
https://stackoverflow.com/questions/60448903/cannot-install-scikit-learn-on-jetson-nano

sudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev liblapack-dev libblas-dev gfortran
sudo apt-get install build-essential cython3
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 ./get-pip.py
python3 -m pip install --upgrade cython
python3 -m pip install --upgrade scikit-image

sudo apt-get install python3-scipy
pip3 install Pillow
pip3 install pyserial
sudo apt-get install python3-matplotlib python3-numpy python3-pil python3-scipy python3-tk
sudo apt-get install build-essential cython3
sudo pip3 install scikit-image
pip3 install python3-pyqt5
sudo pip3 install python3-pyqt5
sudo apt install python3-pyqt5

sudo apt-get install build-essential python3-dev cython3 python3-setuptools python3-pip python3-wheel python3-numpy python3-pytest python3-blosc python3-brotli python3-snappy python3-lz4 libz-dev libblosc-dev liblzma-dev liblz4-dev libzstd-dev libpng-dev libwebp-dev libbz2-dev libopenjp2-7-dev libjpeg-turbo8-dev libjxr-dev liblcms2-dev libcharls-dev libaec-dev libbrotli-dev libsnappy-dev libzopfli-dev libgif-dev libtiff-dev
pip install imagecodecs==2019.5.22
pip install scikit-image==0.16.2



####################New install Jetson get standard installation process######
## sudo no password
## sudo visudo
###  qa     ALL=(ALL) NOPASSWD:ALL


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

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow
python3 -m pip install --upgrade pyserial
python3 -m pip install imagecodecs==2019.5.22
python3 -m pip install scikit-image==0.16.2
python3 -m pip install dataclasses


##low is zero
sudo apt-get update
sudo apt-get install avahi-daemon avahi-discover libnss-mdns
