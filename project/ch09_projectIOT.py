# Ch09 Project IOT — Lift via Stepper Motor & Potmeter, afstand tot grond via Ultrasoon sensor, alle waarden uitleesbaar op Nokia LCD 5110
import cgitb
cgitb.enable()
import spidev
import PIL
import RPi.GPIO as GPIO
import time
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# -- Setup Pi GPIO Numbers --
GPIO.setmode(GPIO.BCM)

# -- Setup Nokia 5110 LCD SPI Config --
DC = 5     # data/control (GPIO5 pin29)
RST = 6    # reset (GPIO6 pin31)
SPI_PORT = 0    # SPI port 0
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
ultrasoon_tra = 17  # GPIO18 (pin12)
ultrasoon_rec = 18  # GPIO18 (pin12)

# -- Setup Pin Setup --
GPIO.setup(ultrasoon_tra, GPIO.OUT)  # Ultrasoon Transmitter as output
GPIO.setup(ultrasoon_rec, GPIO.IN)  # Ultrasoon Receiver as input


# -- Setup Functions --
# read SPI data: 8 possible adc's (0 thru 7)
def readadc(adcnum):
    if (adcnum > 7) or (adcnum < 0):
        return -1
    r = spi.xfer2([1, (8 + adcnum) << 4, 0])
    adcout = ((r[1] & 3) << 8) + r[2]
    return adcout


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

# Pot waarde --> *
def get_pot_tussen(pot):
    if 0 <= pot <= 100:
        return ""
    elif 100 < pot <= 200:
        return "*"
    elif 200 < pot <= 300:
        return "**"
    elif 300 < pot <= 400:
        return "***"
    elif 400 < pot <= 500:
        return "****"
    elif 500 < pot <= 600:
        return "*****"
    elif 600 < pot <= 700:
        return "******"
    elif 700 < pot <= 800:
        return "*******"
    elif 800 < pot <= 900:
        return "********"
    elif 900 < pot <= 1000:
        return "*********"
    else:
        return "**********"


# -- Main Program --
try:
    while True:
        # ----- Ultrasoon Sensor Readings + Print -----
        distance = ultrasoon(ultrasoon_tra, ultrasoon_rec)  # Get the distance
        print("Distance = " + str((round(distance, 2))) + "mm")

        # ----- Potmeter + Print to LCD -----
        pot = readadc(0)    # Get waarde Potmeter from ADC Channel 0
        # Clear LCD Screen
        draw.rectangle((0, 0, LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
        # Write some text
        draw.text((1, 0), "ADC value", font=font)
        draw.text((1, 8), "on display", font=font)
        draw.text((1, 16), "in0=" + str(pot), font=font)
        draw.text((1, 24), str(get_pot_tussen(pot)), font=font)
        disp.image(image)
        disp.display()
        # Print Pot waarde + * reeks
        print("ADC Pot1 = " + str(pot), end="\t")
        print(get_pot_tussen(pot))


except KeyboardInterrupt:
    GPIO.cleanup()
