screwWidth = 40
screwHeight = 40

DEFAULTCONFIG={"cw":3280,"ch":2464,"profilepath":"/home/pi/Desktop/pyUI/profiles"}

IP='192.168.1.12'
URL='http://%s:8888' % IP

PASSWORD='pi'

#IP_LEFT='192.168.1.27'
IP_LEFT='192.168.1.30'
URL_LEFT='http://%s:8888' % IP_LEFT

#IP_RIGHT='192.168.1.26'
IP_RIGHT='192.168.7.2'
URL_RIGHT='http://%s:8080' % IP_RIGHT
#LOCALCMD='sudo ifconfig usb0:avahi 192.168.7.1 netmask 255.255.255.0 up'
LOCALCMD='sudo ifconfig eth0 169.254.248.100 netmask 255.255.0.0 up'

#IP_TOP='192.168.1.25'
IP_TOP='169.254.38.40'
URL_TOP='http://%s:8888' % IP_TOP
