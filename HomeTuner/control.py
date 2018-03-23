import json
import logging
import threading

import RPi.GPIO as GPIO
import pygame.mixer
import time
from config import LED, NEXT_SONG_BUTTON, STOP_BUTTON, REED_SWITCH, BLINK_DELAY, BLINK_TIMES, DOUBLE_PRESS_DELAY, \
    DOUBLE_PRESS_CHECK_INTERVAL, SONGS, DEVICES

logger = logging.getLogger(__name__)


class Circuit:
    def __init__(self):
        self.active = True
        self.playing = False
        self.init_gpio()

    def control_circuit(self):
        toggle_activation = False
        for _ in range(DOUBLE_PRESS_DELAY / DOUBLE_PRESS_CHECK_INTERVAL):
            if GPIO.input(NEXT_SONG_BUTTON) and GPIO.input(STOP_BUTTON):
                # keeping both buttons pressed for DOUBLE_PRESS_DELAY seconds toggles circuit activation.
                toggle_activation = True
                time.sleep(DOUBLE_PRESS_DELAY)
            else:
                toggle_activation = False
                break
        if toggle_activation:
            self.active = not self.active
            if not self.active:
                self.stop_music(switch_led_off=False)
            self.blink_led()
        if not self.active:
            return
        if GPIO.input(REED_SWITCH) and not self.playing:
            self.play_music()
            self.playing = True
        elif GPIO.input(STOP_BUTTON):
            self.stop_music()
            self.playing = False
        elif GPIO.input(NEXT_SONG_BUTTON):
            self.stop_music()
            self.play_music()

    @staticmethod
    def init_gpio():
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(NEXT_SONG_BUTTON, GPIO.IN)
        GPIO.setup(STOP_BUTTON, GPIO.IN)
        GPIO.setup(REED_SWITCH, GPIO.IN)

    def blink_led(self):
        def blink_process(active):
            for _ in range(BLINK_TIMES * 2):
                GPIO.output(LED, GPIO.LOW if active else GPIO.HIGH)
                active = not active
                time.sleep(BLINK_DELAY)
            GPIO.output(LED, GPIO.LOW)

        t = threading.Thread(target=blink_process, args=[self.active])
        t.run()

    def play_music(self):
        song = self.get_song_to_play()
        GPIO.output(LED, GPIO.HIGH)
        pygame.mixer.init(44100, -16, 2, 1024)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()
        logger.info("Started playing song {}.".format(song))

    def stop_music(self, switch_led_off=True):
        if switch_led_off:
            GPIO.output(LED, GPIO.LOW)
        pygame.mixer.music.stop()
        logger.info("Stopping music.")

    def get_song_to_play(self):
        with open(SONGS) as f:
            songs = json.load(f)
        with open(DEVICES) as f:
            devices = json.load(f)
            last_device = devices['last']
    # todo get songs based on last device connected and user playing policy