# Ch09 Project IOT — Lift via Stepper Motor & Potmeter, afstand tot grond via Ultrasoon sensor, alle waarden uitleesbaar op Nokia LCD 5110
import RPi.GPIO as GPIO
import time

# -- Setup Pi GPIO Numbers --
GPIO.setmode(GPIO.BCM)

# -- Setup Pin Variables --
ultrasoon_tra = 17  # GPIO18 (pin12)
ultrasoon_rec = 18  # GPIO18 (pin12)

# -- Setup Pin Setup --
GPIO.setup(ultrasoon_tra, GPIO.OUT)  # Ultrasoon Transmitter as output
GPIO.setup(ultrasoon_rec, GPIO.IN)  # Ultrasoon Receiver as input


# -- Setup Functions --
# Get Distance from Ultrasoon sensor (HC-SR04)
def ultrasoon(trans, receiv):  # Return distance in mm
    GPIO.output(trans, 1)
    time.sleep(0.00001)
    GPIO.output(trans, 0)
    # Wait for the receiver to turn high & get the current time
    while GPIO.input(receiv) == 0:
        time_high = time.time()
    # Wait for the receiver to turn low & get the current time
    while GPIO.input(receiv) == 1:
        time_low = time.time()
    # Get the total passed time between time low & high
    time_passed = time_low - time_high
    return time_passed * 170000


# -- Main Program --
try:
    while True:
        distance = ultrasoon(ultrasoon_tra, ultrasoon_rec)  # Get the distance
        print("Distance = " + str((round(distance, 2))) + "mm")

except KeyboardInterrupt:
    GPIO.cleanup()
