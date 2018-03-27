import logging
import random
import os
import threading
import vlc
import time

from flask import Blueprint, jsonify, render_template, request

from config import LED, STOP_BUTTON, REED_SWITCH, BLINK_DELAY, BLINK_TIMES, LONG_PRESS_TIME, SONGS_DIR, DEFAULT_SONG, \
    INPUT_CHECK_INTERVAL, EXIT_HOUSE_TIMER, INPUT_CHECK_TIMES
from HomeTuner.util import file_handler
from HomeTuner.util import get_guest_name

try:
    import RPi.GPIO as GPIO
except ImportError:
    import GPIOEmu as GPIO

logger = logging.getLogger(__name__)
player = Blueprint("player", __name__)


class Circuit:
    def __init__(self):
        self.active = True
        self.playing = False
        self.stop_button_press_time = 0
        self.player = None
        self.callbacks = {
            STOP_BUTTON: self.handle_stop_button,
            REED_SWITCH: self.play_music
        }
        # GPIO init
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(STOP_BUTTON, GPIO.IN)
        GPIO.setup(REED_SWITCH, GPIO.IN)
        GPIO.add_event_detect(STOP_BUTTON, GPIO.BOTH, callback=self.check_input_before_callback)
        GPIO.add_event_detect(REED_SWITCH, GPIO.RISING, callback=self.check_input_before_callback)
        self.switch_led_off()

    @staticmethod
    def light_led_up():
        GPIO.output(LED, GPIO.HIGH)

    @staticmethod
    def switch_led_off():
        GPIO.output(LED, GPIO.LOW)

    def play_music(self, song=None, start=None):
        if self.playing:
            return # avoids multiple triggering
        self.stop_music()
        if not song or start is None:
            song, start = self.update_song_queue()
        self.player = vlc.MediaPlayer(song)
        self.player.play()
        self.player.set_time(start * 1000)
        logger.info("Started playing song {}.".format(song))
        # LED blink
        self.playing = True

        def play_until_music_stops(circuit):
            counter = 0
            while circuit.playing:
                circuit.switch_led_off() if counter % 2 == 1 else circuit.light_led_up()
                counter += 1
                time.sleep(BLINK_DELAY)
            circuit.switch_led_off()

        t = threading.Thread(target=play_until_music_stops, args=[self])
        t.start()

    def stop_music(self):
        self.stop_button_press_time = time.time()
        if self.playing:
            logger.info("Stopping music.")
            self.playing = False
            self.player.stop()

    @staticmethod
    def update_song_queue():
        data = file_handler.read_data_file()
        last_device = data['lastDevice']
        now_playing = data['devices'][last_device]['nextSong']
        start = data['devices'][last_device]['songs'].get(now_playing, 0)
        songs = list(data['devices'][last_device]['songs'].keys())
        try:
            if data['devices'][last_device]['playingOrder'] == 'random':
                data['devices'][last_device]['nextSong'] = random.choice(songs)
            else:
                data['devices'][last_device]['nextSong'] = (songs.index(now_playing) + 1) % len(songs)
        except IndexError:
            data['devices'][last_device]['nextSong'] = DEFAULT_SONG
        return os.path.join(SONGS_DIR, "{}.mp3".format(now_playing)), start

    def suspend(self, suspend_time=EXIT_HOUSE_TIMER):
        self.active = False

        def blink_exit():
            for i in range(suspend_time * 2):
                self.switch_led_off() if i % 2 == 1 else self.light_led_up()
                time.sleep(0.5)
            self.active = True

        t = threading.Thread(target=blink_exit)
        t.start()
        logger.info("Circuit is disabled for {} seconds".format(suspend_time))

    def check_input_before_callback(self, channel):
        if not self.active:
            return
        value = GPIO.input(channel)
        for _ in range(INPUT_CHECK_TIMES):
            time.sleep(INPUT_CHECK_INTERVAL)
            if value != GPIO.input(channel):
                # my pi detects random current spikes that trigger music randomly, just checking input twice here
                return
        else:
            self.callbacks[channel]()

    def handle_stop_button(self):
        if GPIO.input(STOP_BUTTON):
            self.stop_music()
            self.suspend(suspend_time=2)
        else:
            if self.stop_button_press_time + LONG_PRESS_TIME > time.time():
                return  # button hasn't been pressed long enough
            else:
                self.suspend()


circuit = Circuit()


@player.route("/suspend")
def suspend_circuit():
    """
    Suspends the circuits for some seconds, allowing the user to exit the house without playing the song.
    """
    circuit.suspend()
    return render_template("suspend.html", seconds=EXIT_HOUSE_TIMER, name=get_guest_name())


def main():
    pass


if __name__ == '__main__':
    main()
