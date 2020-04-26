import picamera
from flask import Flask, request, send_file
import time
import io
from PIL import Image
import threading
import logging
import sys
import RPi.GPIO as gp
from datetime import datetime
import os

app = Flask(__name__)
quit_event = threading.Event()
pause_event = threading.Event()
save_image_event = threading.Event()
save_complete_event = threading.Event()
image_ready = io.BytesIO()
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def Init():
    gp.setwarnings(False)
    gp.setmode(gp.BOARD)

    gp.setup(7, gp.OUT)
    gp.setup(11, gp.OUT)
    gp.setup(12, gp.OUT)

    gp.setup(15, gp.OUT)
    gp.setup(16, gp.OUT)
    gp.setup(21, gp.OUT)
    gp.setup(22, gp.OUT)

    gp.output(11, True)
    gp.output(12, True)
    gp.output(15, True)
    gp.output(16, True)
    gp.output(21, True)
    gp.output(22, True)

    print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera")
    i2c = "i2cset -y 1 0x70 0x00 0x04"
    os.system(i2c)
    gp.output(7, False)
    gp.output(11, False)
    gp.output(12, True)

#@pyjsonrpc.rpcmethod
def Uninit():
    gp.output(7, False)
    gp.output(11, False)
    gp.output(12, True)

def preview():
    global image_ready
    while True:
        logging.info("preview: thread is starting...")
        pause_event.wait()
        pause_event.clear()
        if quit_event.is_set():
            break
        Init()
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.ISO = 50
            camera.resolution=(640,480)
            #camera.start_preview()
            #time.sleep(2)
            for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
                stream.seek(0)
                image = Image.open(stream)
                if save_image_event.is_set():
                    # with open("foo.jpg", "w") as f:                
                    #     image.save(f)
                    if image_ready is None or image_ready.closed:
                        image_ready = io.BytesIO()
                    else:
                        image_ready.seek(0)
                        image_ready.truncate()
                    image.save(image_ready, format='JPEG')
                    save_complete_event.set()
                    save_image_event.clear()
                stream.seek(0)
                stream.truncate()
                if pause_event.is_set():
                    pause_event.clear()
                    break
        if quit_event.is_set():
            break
    logging.info("preview: thread is terminated")

@app.route('/')
def hello_world():
    # return 'post data to http://10.1.1.154:5000/sga'
    #return render_template('home.html')
    return "Hello, World!"

@app.route('/preview')
def preview_getimage():
    save_image_event.set()
    save_complete_event.wait()
    save_complete_event.clear()
    image_ready.seek(0)
    return send_file(image_ready, mimetype='image/jpeg')

@app.route('/startpause')
def start_pause():
    pause_event.set()
    return "OK"

@app.route('/shutdown')
def shutdown():
    quit_event.set()
    pause_event.set()
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    logging.info("main: is terminating...")
    return 'Server shutting down...'

if __name__ == '__main__':
    logging.info("main: is starting.")
    t = threading.Thread(target=preview, daemon=True)
    t.start()
    app.run(host='0.0.0.0')
    logging.info("main: shutdown preview thread.")
    quit_event.set()
    pause_event.set()
    t.join()
    logging.info("main: is terminated.")