import RPi.GPIO as GPIO

class GenericButtonHandler:
    def __init__(self, input_pin, output_pin):
        self.input_pin = input_pin
        self.output_pin = output_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.output_pin, GPIO.OUT, initial=GPIO.LOW)

        GPIO.add_event_detect(
            self.input_pin, 
            GPIO.RISING, 
            callback=self.trigger, 
            bouncetime=200
        )

    def trigger(self, pin):
        if GPIO.input(pin) == GPIO.HIGH:
            current_state = GPIO.input(self.output_pin)
            GPIO.output(self.output_pin, not current_state)
