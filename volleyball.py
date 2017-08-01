# To use:
#  install omxplayer-python-wrapper: https://github.com/willprice/python-omxplayer-wrapper
#    Before this, run sudo apt-get install libdbus-glib-1-dev libdbus-1-dev
#    Make sure you run sudo pip3 install dbus-python because by default it is only installed for Python 2
# I have only tried this with Python3.4 (which comes pre-installed on Raspbian Jesse.
# TODO use step for frame seeking
from dbus.exceptions import DBusException 
from omxplayer import OMXPlayer
from time import sleep
import picamera
import subprocess
import os
import termios
import sys
import time
import termios, fcntl, sys, os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
# Don't use a pull up or pull down because that's usually used
# for mechanicaly switches, and our chip's output is well-defined.

QUIT_BUTTON = 8
channels = [QUIT_BUTTON, 10, 11, 12, 13]
for channel in channels:
    GPIO.setup(channel, GPIO.IN)
    
file_path_or_url = '/home/pi/Videos' + time.strftime('%Y-%m-%d-%H:%M:%S') + '.mpg'

seekers = {
    12: -3000000,
    13: -10000000,
}

fd = sys.stdin.fileno()

oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)


# Remove the old file (maybe someday we should make a copy of it...)
if os.path.exists(file_path_or_url):
    os.remove(file_path_or_url)
    print("file removed.")

# start the ffmpeg process with a pipe for stdin
ffmpeg = subprocess.Popen([
    'ffmpeg', '-i', '-',
    '-vcodec', 'copy',
    '-an', file_path_or_url,
    ], stdin=subprocess.PIPE)

# initialize the camera
camera = picamera.PiCamera(resolution=(800, 480), framerate=25)

# start recording to ffmpeg's stdin
camera.start_recording(ffmpeg.stdin, format='h264', bitrate=2000000)
camera.start_preview()
camera.rotation = 90

class Engine:
    player = None
    done = False
    
    def stop_player(self):
        if self.player:
            self.player.quit()
    def initialize_player(self):
        camera.stop_preview()
        self.player = OMXPlayer(file_path_or_url, ['--win', '0,0,800,480'])

    def button_callback(self, channel):
        if GPIO.input(channel):
            self.button_released(channel)
        else:
            self.button_pressed(channel)
            
    def button_released(self, channel):
        print('released!' + str(channel))
        if channel is QUIT_BUTTON:
            if time.time() - self.quitPressed > 1:
                print('done')
                engine.done = True
            else:
                print('live')
                self.player.stop()
                camera.start_preview()
                
    def button_pressed(self, channel):
        print('pressed!' + str(channel))
        if channel is QUIT_BUTTON:
            self.quitPressed = time.time()
        elif channel is 11 and self.player:
            self.player.action(23) # Step
        elif channel is 10 and self.player:
            print('play/pause')
            if self.player:
                self.player.play_pause()
            else:
                self.initialize_player()
        elif channel in seekers:
            print('seek')
            firstTime = False
            if self.player is None:
                self.initialize_player()
                firstTime = True
            elif not self.player.position():
                # player.position() will be None when the player
                # is done playing. For some reason, that works but
                # player.playback_status() returns "Paused"
                # instead of "Stopped".
                self.player.load(file_path_or_url)
                firstTime = True
            toSeek = seekers[channel]
            if toSeek < 0 and firstTime:
                # Seek from the end of the video.
                print(self.player.duration())
                newPos = max(self.player.duration() + toSeek / 1000000, 0)
                print('Seeking to absolute pos ' + str(newPos))
                self.player.set_position(newPos)
            else:
                self.player.seek(toSeek)
            camera.stop_preview()
            
engine = Engine()
for channel in channels:
    GPIO.add_event_detect(channel, GPIO.BOTH, callback=engine.button_callback)

try: 
    while not engine.done:
        try:
            if not camera.preview and engine.player and not engine.player.playback_status():
                print(str(engine.player.playback_status()))
                camera.start_preview()
        except DBusException:
            print('Got DBusException, continuing')
# Kill the `omxplayer` process gracefully.
finally:
    if camera:
        camera.stop_recording()
    ffmpeg.stdin.close()
    ffmpeg.kill()
    engine.stop_player
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

