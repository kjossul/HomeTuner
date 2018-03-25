import logging
import random
import os
import threading
import vlc
import time

from flask import Blueprint, jsonify, render_template, request

from config import LED, STOP_BUTTON, REED_SWITCH, BLINK_DELAY, BLINK_TIMES, LONG_PRESS_TIME, SONGS_DIR, DEFAULT_SONG, \
    SWITCH_CHECK_INTERVAL, EXIT_HOUSE_TIMER
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
        self.active = False
        self.playing = False
        self.disable_buttons = False
        self.stop_button_press_time = 0
        self.player = None
        # GPIO init
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(STOP_BUTTON, GPIO.IN)
        GPIO.setup(REED_SWITCH, GPIO.IN)
        GPIO.add_event_detect(STOP_BUTTON, GPIO.BOTH, callback=self.handle_stop_button)
        GPIO.add_event_detect(REED_SWITCH, GPIO.RISING, callback=self.play_music)
        # activate
        self.toggle_activation()

    @staticmethod
    def light_led_up():
        GPIO.output(LED, GPIO.HIGH)

    @staticmethod
    def switch_led_off():
        GPIO.output(LED, GPIO.LOW)

    def toggle_activation(self):
        if self.stop_button_press_time + LONG_PRESS_TIME > time.time():
            return  # button hasn't been pressed long enough
        for _ in range(BLINK_TIMES * 2 - 1):
            self.switch_led_off() if self.active else self.light_led_up()
            self.active = not self.active
            time.sleep(BLINK_DELAY)

    def play_music(self, channel=None, song=None, start=None):
        time.sleep(SWITCH_CHECK_INTERVAL)
        if not self.active or not GPIO.input(REED_SWITCH):
            # return if the switch is not closed, avoids random current spikes to be picked up by this function
            return
        self.stop_music()
        if not song or not start:
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
                circuit.switch_led_off() if counter % 2 == 0 else circuit.light_led_up()
                counter += 1
                time.sleep(BLINK_DELAY)
            circuit.light_led_up()

        t = threading.Thread(target=play_until_music_stops, args=[self])
        t.start()

    def stop_music(self):
        self.stop_button_press_time = time.time()
        if self.playing:
            logger.info("Stopping music.")
        self.playing = False
        try:
            self.player.stop()
        except Exception:
            pass

    def update_song_queue(self):
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

    def handle_stop_button(self, channel=None):
        if GPIO.input(STOP_BUTTON):
            self.stop_music()
        else:
            self.toggle_activation()


circuit = Circuit()


@player.route("/suspend")
def suspend_circuit():
    """
    Suspends the circuits for some seconds, allowing the user to exit the house without playing the song.
    """
    circuit.active = False

    def blink_exit():
        for i in range(EXIT_HOUSE_TIMER * 2):
            circuit.switch_led_off() if i % 2 == 0 else circuit.light_led_up()
            time.sleep(0.5)
        circuit.active = True

    t = threading.Thread(target=blink_exit)
    t.start()
    return render_template("suspend.html", seconds=EXIT_HOUSE_TIMER, name=get_guest_name())


@player.route('/play')
def play_song():
    data = request.get_json()


def main():
    pass


if __name__ == '__main__':
    main()
