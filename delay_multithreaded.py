# import the necessary packages
from __future__ import print_function
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import imutils
import time
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--num-frames", type=int, default=100,
	help="# of frames to delay")
args = vars(ap.parse_args())


# allow the camera to warmup and start the FPS counter
print("[INFO] sampling frames from `picamera` module...")
time.sleep(2.0)

# created a *threaded *video stream, allow the camera sensor to warmup,
# and start the FPS counter
print("[INFO] sampling THREADED frames from `picamera` module...")
vs = PiVideoStream().start()
time.sleep(2.0)
fps = FPS().start()

index = 0
frames = []
delay = args["num_frames"]
# loop over some frames...this time using the threaded stream
while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	frame = vs.read()
	# frame = imutils.resize(frame, width=400)
        if (len(frames) <= index):
            frames.append(frame)
        else:
            cv2.imshow("Frame", frames[index])
            # Note that we explicitly wait for longer than 1
            # second because this thread was processing the
            # frames too quickly, resulting in many duplicates
            # being put into the delay array.
            key = cv2.waitKey(10) & 0xFF
            if key == ord("q"):
                break
            frames[index] = frame
        index += 1
        if index > delay:
            index = 0
	# update the FPS counter
	fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
