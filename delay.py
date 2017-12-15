# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
 
# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 20
rawCapture = PiRGBArray(camera, size=(640, 480))
 
# allow the camera to warmup
time.sleep(0.1)

index = 0
frames = []

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image, then
	# initialize the timestamp and occupied/unoccupied text
	image = frame.array

        if (len(frames) <= index):
            frames.append(frame.array)
        else:
            # show the frame
            cv2.imshow("Frame", frames[index])
            key = cv2.waitKey(1) & 0xFF
            frames[index] = frame.array
        index += 1
        if index > 29:
            index = 0
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)
 
