import RPi.GPIO as GPIO

def setup_button(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN)
    GPIO.add_event_detect(pin, GPIO.RISING, callback=button_callback, bouncetime=200)
    return True

def button_callback(pin):
    print(f"Button on pin {pin} was pressed!")
    return True

def clear_led(pin):
    GPIO.cleanup(pin)
    GPIO.remove_event_detect(pin)