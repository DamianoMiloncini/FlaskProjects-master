
import RPi.GPIO as GPIO
from time import sleep

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
LED = 17
LED2 = 19
LED3 = 25

GPIO.setup(LED, GPIO.OUT)
GPIO.setup(LED2,GPIO.OUT)
GPIO.setup(LED3,GPIO.OUT)

while True:
    GPIO.output(LED,GPIO.HIGH)
    GPIO.output(LED2,GPIO.LOW)
    GPIO.output(LED3,GPIO.LOW)
    sleep(0.5)
    GPIO.output(LED,GPIO.HIGH)
    GPIO.output(LED2,GPIO.HIGH)
    GPIO.output(LED3,GPIO.LOW)
    sleep(0.5)
    GPIO.output(LED,GPIO.HIGH)
    GPIO.output(LED2,GPIO.HIGH)
    GPIO.output(LED3,GPIO.HIGH)
    sleep(0.5)
    GPIO.output(LED,GPIO.LOW)
    GPIO.output(LED2,GPIO.HIGH)
    GPIO.output(LED3,GPIO.HIGH)
    sleep(0.5)
    GPIO.output(LED,GPIO.LOW)
    GPIO.output(LED2,GPIO.LOW)
    GPIO.output(LED3,GPIO.HIGH)
    sleep(0.5)
    GPIO.output(LED,GPIO.LOW)
    GPIO.output(LED2,GPIO.LOW)
    GPIO.output(LED3,GPIO.LOW)










