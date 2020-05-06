# Ch09 Project IOT — Lift via Stepper Motor & Potmeter, afstand tot grond via Ultrasoon sensor, alle waarden uitleesbaar op Nokia LCD 5110
import sys
import spidev
import PIL
import RPi.GPIO as GPIO
import time
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import json
import requests
import _thread

# import cgitb
# cgitb.enable()

# -- Setup Pi GPIO Numbers --
GPIO.setmode(GPIO.BCM)

# -- Setup Nokia 5110 LCD SPI Config --
DC = 5  # data/control (GPIO5 pin29)
RST = 6  # reset (GPIO6 pin31)
SPI_PORT = 0  # SPI port 0
SPI_DEVICE = 1  # CS1 (GPIO7 pin26)
# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))

# -- Setup ADC SPI --
spi = spidev.SpiDev()  # create spi object
spi.open(0, 0)  # SPI port 0, device CS0 (GPIO8 pin24)
spi.max_speed_hz = (1000000)

# -- Setup Nokia 5110 LCD Settings --
# Initialize library
disp.begin(contrast=50)
# Clear display
disp.clear()
disp.display()
# Load default font
font = ImageFont.load_default()
# Get drawing object to draw on image
draw = ImageDraw.Draw(image)
# Draw a white filled box to clear image
draw.rectangle((0, 0, LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)

# ------ Setup Pin Variables ------
# Setup Ultrasoon Sensor Pins
ultrasoon_tra = 17  # GPIO18 (pin12)
ultrasoon_rec = 18  # GPIO18 (pin12)
# Setup Stepper Pins
Stepper_A = 27  # GPIO27 (pin13)
Stepper_B = 22  # GPIO22 (pin15)
Stepper_C = 23  # GPIO23 (pin16)
Stepper_D = 24  # GPIO24 (pin18)

# -- Setup Pin Setup --
# Setup Ultrasoon Sensor Pins
GPIO.setup(ultrasoon_tra, GPIO.OUT)  # Ultrasoon Transmitter as output
GPIO.setup(ultrasoon_rec, GPIO.IN)  # Ultrasoon Receiver as input
# Setup Stepper Pins
GPIO.setup(Stepper_A, GPIO.OUT)  # Stepper A as output
GPIO.setup(Stepper_B, GPIO.OUT)  # Stepper B as output
GPIO.setup(Stepper_C, GPIO.OUT)  # Stepper C as output
GPIO.setup(Stepper_D, GPIO.OUT)  # Stepper D as output

# ------ UBEAC User Info ------
url = "TEMP_URL"
uid = "TEMP_ID"

# -- Setup variables --
# Set min & max height
height_min = 3
height_max = 16
# Max Margin between current & needed height
margin = 0.5
# Setup delay_stepper between Steps (1 = 1ms)
delay_stepper = 0.1
# delay_stepper to ms
delay_ms_stepper = delay_stepper / 1000
# Full Step motor pattern
stepper_FullStep = [(1, 0, 0, 0),
                    (1, 1, 0, 0),
                    (0, 1, 0, 0),
                    (0, 1, 1, 0),
                    (0, 0, 1, 0),
                    (0, 0, 1, 1),
                    (0, 0, 0, 1),
                    (1, 0, 0, 1)]

# Global variables
stepper_state = ""
pot = 0.0
distance = 0.0
needed = 0.0


# -- Setup Functions --
# read SPI data: 8 possible adc's (0 thru 7)
def readadc(adcnum):
    if (adcnum > 7) or (adcnum < 0):
        return -1
    r = spi.xfer2([1, (8 + adcnum) << 4, 0])
    adcout = ((r[1] & 3) << 8) + r[2]
    return adcout


# Sent data to UBEAC
def sent_ubeac(channel, channelname):
    data = {
        "id": uid,
        "sensors": [{
            'id': channelname,
            'data': channel
        }]
    }
    r = requests.post(url, verify=False, json=data)
    print(r.status_code, channel)
    time.sleep(1)


# Get Distance from Ultrasoon sensor (HC-SR04)
def ultrasoon(trans, receiv):  # Return distance in cm
    global time_high, time_low
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
    return time_passed * 17000


# Pot waarde --> *
def get_pot_tussen(pot_value):
    if 0 <= pot_value <= 100:
        return ""
    elif 100 < pot_value <= 200:
        return "*"
    elif 200 < pot_value <= 300:
        return "**"
    elif 300 < pot_value <= 400:
        return "***"
    elif 400 < pot_value <= 500:
        return "****"
    elif 500 < pot_value <= 600:
        return "*****"
    elif 600 < pot_value <= 700:
        return "******"
    elif 700 < pot_value <= 800:
        return "*******"
    elif 800 < pot_value <= 900:
        return "********"
    elif 900 < pot_value <= 1000:
        return "*********"
    else:
        return "**********"


# Stepper --> Forward
def forward_step(delay):
    for step in stepper_FullStep:
        set_stepper(step, delay)


# Stepper --> Backwards
def backwards_step(delay):
    # Go trough "stepper_FullStep" in reverse order
    for step in stepper_FullStep[::-1]:
        set_stepper(step, delay)


# Stepper - Step list
def set_stepper(step_list, delay):
    GPIO.output(Stepper_A, step_list[0])
    GPIO.output(Stepper_B, step_list[1])
    GPIO.output(Stepper_C, step_list[2])
    GPIO.output(Stepper_D, step_list[3])
    time.sleep(delay)


def get_height_needed(pot_value, height_min, height_max):
    height_total = height_max - height_min
    return (
                       height_total * pot_value / 100) + height_min  # Calculate Target Distance based on Potmeter Value & set Correct min height


# ----- Multithreading stuff -----
# Define functions for each thread
# -- Stepper Motor control based on height
def steppermotor(threadName, delay, margin):
    global stepper_state
    global pot
    global distance
    try:
        while True:
            height_needed = get_height_needed(pot, height_min, height_max)
            if abs(distance - height_needed) > margin:
                if distance > height_needed:  # If current distance is higher than Target distance
                    backwards_step(delay)  # Lift goes down
                    stepper_state = "Down"
                else:  # If current distance is lower than Target distance
                    forward_step(delay)  # Lift goes up
                    stepper_state = "Up"
            else:
                stepper_state = "Idle"

    except KeyboardInterrupt:
        print(threadName + "Stopped")
        GPIO.cleanup()


# -- Ultrasoon Sensor + Potmeter readings --
def Sensor_readings(threadName, delay):
    global distance
    global needed
    global pot
    try:
        while True:
            # ----- Ultrasoon Sensor Readings -----
            distance = ultrasoon(ultrasoon_tra, ultrasoon_rec)  # Get the distance in cm
            needed = get_height_needed(pot, height_min, height_max)  # Get the target distance in cm
            # ----- Potmeter -----
            pot = readadc(0) / 1023 * 100  # Get waarde Potmeter from ADC Channel 0
            time.sleep(delay)

    except KeyboardInterrupt:
        print(threadName + "Stopped")
        GPIO.cleanup()


# -- Sent Data to UBEAC --
def UBEAC_Sent(threadName, delay):
    try:
        while True:
            # ----- Sent to UBEAC -----
            # sent_ubeac(distance, 'Distance Platform')
            time.sleep(delay)

    except KeyboardInterrupt:
        print(threadName + "Stopped")
        GPIO.cleanup()


# -- Start separate threads --
try:
    _thread.start_new_thread(steppermotor, ("StepperMotor-Thread", delay_ms_stepper, margin))
    _thread.start_new_thread(Sensor_readings, ("Sensor_readings-Thread", 0.5))
    _thread.start_new_thread(UBEAC_Sent, ("UBEAC_Sent-Thread", 2))

except:
    sys.exit("Error: unable to start threads")

# -- Main Program --
# TODO: Add Calibration section, min & max height (Optional if Hardcoded values)
# TODO: Optimise 'get_pot_tussen', multiply '*' by value derived from % (Single 'Return')
# TODO: Multithread the application (Stepper done)
try:
    while True:
        # ----- Print to LCD -----
        # Clear LCD Screen
        draw.rectangle((0, 0, LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
        # Write data to Screen
        draw.text((1, 0), "Stepper: " + stepper_state, font=font)  # Write the Stepper State (Idle, Up, Down)
        draw.text((1, 8), "POT: " + str(round(pot, 2)) + "%", font=font)  # Write the Potmeter Value in %
        draw.text((1, 16), str(get_pot_tussen(pot * 1023 / 100)),
                  font=font)  # Write the * reeks based on the Potmeter Value
        draw.text((1, 24), "Dist: " + str(round(distance, 1)) + "cm", font=font)  # Write the current distance in cm
        draw.text((1, 32), "Need: " + str(round(needed, 1)) + "cm", font=font)  # Write the Target Distance in cm
        disp.image(image)
        disp.display()

        # ----- Print to Console -----
        print("Stepper: " + stepper_state)  # Write the Stepper State (Idle, Up, Down)
        print("POT: " + str(round(pot, 2)) + "%", end="\t")  # Write the Potmeter Value in %
        print(get_pot_tussen(pot * 1023 / 100))  # Write the * reeks based on the Potmeter Value
        print("Distance: " + str(round(distance, 2)) + "cm")  # Write the current distance in cm
        print("Needed: " + str(round(needed, 1)) + "cm")  # Write the Target Distance in cm
        print()

except KeyboardInterrupt:
    GPIO.cleanup()
