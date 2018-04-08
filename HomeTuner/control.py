import logging
import random
import os
import threading
import vlc
import time

from flask import Blueprint, render_template

from config import LED, STOP_BUTTON, REED_SWITCH, BLINK_DELAY, LONG_PRESS_TIME, SONGS_DIR, DEFAULT_SONG, \
    INPUT_CHECK_INTERVAL, EXIT_HOUSE_TIMER
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
        GPIO.add_event_detect(STOP_BUTTON, GPIO.BOTH, callback=self.check_input_before_callback, bouncetime=5)
        GPIO.add_event_detect(REED_SWITCH, GPIO.RISING, callback=self.check_input_before_callback, bouncetime=5)
        self.switch_led_off()

    @staticmethod
    def light_led_up():
        GPIO.output(LED, GPIO.HIGH)

    @staticmethod
    def switch_led_off():
        GPIO.output(LED, GPIO.LOW)

    def play_music(self, song=None, start=None, quiet=False):
        time.sleep(0.5)
        if self.playing or not self.active or not GPIO.input(REED_SWITCH):
            return
        self.stop_music()
        if not song or start is None:
            song, start = self.update_song_queue()
        self.player = vlc.MediaPlayer(song)
        if quiet:
            self.player.audio_set_volume(10)
            self.playing = False
        else:
            self.player.audio_set_volume(100)
            self.playing = True
        self.player.play()
        self.player.set_time(start * 1000)
        logger.info("Started playing song {}.".format(song))
        # LED blink

        def play_until_music_stops(circuit):
            counter = 0
            while circuit.playing and counter < (1 / BLINK_DELAY) * 60 * 3:  # after 3 minutes it stops music
                circuit.switch_led_off() if counter % 2 == 1 else circuit.light_led_up()
                counter += 1
                time.sleep(BLINK_DELAY)
            circuit.switch_led_off()
            self.stop_music()

        t = threading.Thread(target=play_until_music_stops, args=[self])
        t.start()
        if quiet:
            time.sleep(10)
            self.player.stop()

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
        value = GPIO.input(channel)
        time.sleep(INPUT_CHECK_INTERVAL)
        if value != GPIO.input(channel):
            # my pi detects random current spikes that trigger music randomly, just checking input twice here
            return
        else:
            self.callbacks[channel]()

    def handle_stop_button(self):
        if GPIO.input(STOP_BUTTON):
            self.stop_music()
        else:
            diff = time.time() - self.stop_button_press_time
            if diff < LONG_PRESS_TIME or diff > LONG_PRESS_TIME * 2:
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
