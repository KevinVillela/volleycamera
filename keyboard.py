# This is the version that is controlled by the keyboard.
# Just saving it now because I am too lazy to use version control for now.
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

import termios, fcntl, sys, os

file_path_or_url = '/home/pi/test.mpg'

seekers = {
    ',': -1000,
    '.': 1000,
    'j': -3000000,
    'l': 3000000,
    'h': -10000000,
    ';': 10000000,
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

player = None

try:
    while 1:
        try:
            char = sys.stdin.read(1)
            if char:
                print(repr(char))
            if player and not player.position() and not camera.previewing:
                desperate = False
                camera.start_preview()
            if char is '':
                break
            if char is 'q' and player:
                player.stop()
                camera.start_preview()
            elif char is ' ' and player:
                player.play_pause()
            elif char in seekers:
                camera.stop_preview()
                firstTime = False
                if player is None:
                    # This will start an `omxplayer` process, this might
                    # fail the first time you run it, currently in the
                    # process of fixing this though.
                    player = OMXPlayer(file_path_or_url, ['--win', '0,0,800,480'])
                    firstTime = True
                elif not player.position():
                    # player.position() will be None when the player
                    # is done playing. For some reason, that works but
                    # player.playback_status() returns "Paused"
                    # instead of "Stopped".
                    player.load(file_path_or_url)
                    firstTime = True
                toSeek = seekers[char]
                if toSeek < 0 and firstTime:
                    # Seek from the end of the video.
                    print(player.duration())
                    newPos = max(player.duration() + toSeek / 1000000, 0)
                    print('Seeking to absolute pos ' + str(newPos))
                    player.set_position(newPos)
                    desperate = True
                else:
                    player.seek(toSeek)
        except DBusException:
            print('Got a DBusException. Moving on')
        except IOError: pass
# Kill the `omxplayer` process gracefully.
finally:
    if camera:
        camera.stop_recording()
    ffmpeg.stdin.close()
    ffmpeg.kill()
    if player:
        player.quit()
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

