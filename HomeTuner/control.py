import logging
import threading
from mutagen import mp3
import os
import pygame.mixer
import time
from config import LED, NEXT_SONG_BUTTON, STOP_BUTTON, REED_SWITCH, BLINK_DELAY, BLINK_TIMES_ACTIVATION, \
    BLINK_TIMES_DEACTIVATION, DOUBLE_PRESS_TIME, BUTTON_PRESS_CHECK_INTERVAL, SONGS_DIR
from HomeTuner.util import file_handler

try:
    import RPi.GPIO as GPIO
except ImportError:
    import GPIOEmu as GPIO

logger = logging.getLogger(__name__)


class Circuit:
    def __init__(self):
        self.active = True
        self.playing = False
        self.inputs = {NEXT_SONG_BUTTON: 0,
                       STOP_BUTTON: 0,
                       REED_SWITCH: 0}
        self.buttons = [NEXT_SONG_BUTTON, STOP_BUTTON]
        self.disable_buttons = False
        self.init_controller()

    def check_inputs(self):
        for input in self.inputs:
            self.inputs[input] = GPIO.input(input)
        # keeps buttons disabled if the button is still being pressed
        self.disable_buttons = self.disable_buttons and any(self.inputs[i] for i in self.buttons)

    def control(self):
        toggle_activation = False
        self.check_inputs()
        for _ in range(int(DOUBLE_PRESS_TIME / BUTTON_PRESS_CHECK_INTERVAL)):
            if self.inputs[NEXT_SONG_BUTTON] and self.inputs[STOP_BUTTON]:
                # keeping both buttons pressed for DOUBLE_PRESS_DELAY seconds toggles circuit activation.
                toggle_activation = True
                time.sleep(BUTTON_PRESS_CHECK_INTERVAL)
            else:
                toggle_activation = False
                break
        if toggle_activation:
            self.active = not self.active
            if not self.active:
                self.stop_music(switch_led_off=False)
            self.blink_led(times=BLINK_TIMES_ACTIVATION if self.active else BLINK_TIMES_DEACTIVATION)
        if not self.active:
            return
        if GPIO.input(REED_SWITCH) and not self.playing:
            self.play_music()
            self.playing = True
        elif self.disable_buttons:
            return
        elif GPIO.input(STOP_BUTTON) and self.playing:
            self.stop_music()
            self.playing = False
            self.disable_buttons = True
        elif GPIO.input(NEXT_SONG_BUTTON):
            self.stop_music()
            self.play_music()
            self.next_song = True
            self.disable_buttons = True

        # todo modify to use events instead
    @staticmethod
    def init_controller():
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(NEXT_SONG_BUTTON, GPIO.IN)
        GPIO.setup(STOP_BUTTON, GPIO.IN)
        GPIO.setup(REED_SWITCH, GPIO.IN)

    @staticmethod
    def light_led_up():
        GPIO.output(LED, GPIO.HIGH)

    @staticmethod
    def switch_led_off():
        GPIO.output(LED, GPIO.LOW)

    def blink_led(self, times):
        def blink_process(active):
            for _ in range(times * 2):
                self.switch_led_off() if active else self.light_led_up()
                active = not active
                time.sleep(BLINK_DELAY)
            self.switch_led_off()

        t = threading.Thread(target=blink_process, args=[self.active])
        t.run()

    def play_music(self):
        self.light_led_up()
        song = self.update_song_queue()
        mp3file = mp3.MP3(song)
        pygame.mixer.init(frequency=mp3file.info.sample_rate)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()
        logger.info("Started playing song {}.".format(song))

    def stop_music(self, switch_led_off=True):
        if switch_led_off:
            self.switch_led_off()
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except pygame.error:
            pass
        logger.info("Stopping music.")

    def update_song_queue(self):
        data = file_handler.read_data_file()
        last_device = data['last_device']
        now_playing = data['devices'][last_device]['next_song']
        return os.path.join(SONGS_DIR, now_playing)


def main():
    circuit = Circuit()
    while True:
        circuit.control()
        time.sleep(BUTTON_PRESS_CHECK_INTERVAL)


if __name__ == '__main__':
    main()
