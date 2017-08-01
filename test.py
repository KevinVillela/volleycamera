import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.IN) #, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(10, GPIO.IN) #, pull_up_down=GPIO.PUD_DOWN)

def motion_detected(channel):
    print('Callback!' + str(GPIO.input(8)))
    
def motion_detected_2(channel):
    print('Callback2!' + str(GPIO.input(10)))

GPIO.add_event_detect(8, GPIO.FALLING, callback=motion_detected)
GPIO.add_event_detect(10, GPIO.FALLING, callback=motion_detected_2)
while True:
    pass
#    print('first:' + str(GPIO.input(8)) + ', second: ' + str(GPIO.input(10)))
