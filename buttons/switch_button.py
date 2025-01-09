import RPi.GPIO as GPIO

from button import GenericButtonHandler


class SwitchButton(GenericButtonHandler):
    def trigger(self, pin):
        if GPIO.input(pin) == GPIO.HIGH:
            current_state = GPIO.input(self.output_pin)
            GPIO.output(self.output_pin, not current_state)
