# Flask
DEBUG = False
HOST = '0.0.0.0'
# Flask-Bootstrap
BOOTSTRAP_SERVE_LOCAL = True
# HomeTuner
import os


def get_api_key():
    with open(".apikey") as f:
        api_key = f.read()
    return api_key


INTERFACE = "eno1"  # interface scanned by arp-scan
LAST_SEEN_INTERVAL = 300  # device is considered online if last connection was at most this amount of seconds ago
SLEEP_SECONDS = 1  # seconds between each arp-scan
DUMMY_MAC = "aa:aa:aa:aa:aa"  # fake MAC address for testing, etc
# Directories and generated files
USER_DIR = os.path.expanduser('~/Documents/HomeTuner')
SONGS_DIR = os.path.join(USER_DIR, 'Music')
DATA_FILE = os.path.join(USER_DIR, "data.json")
DEFAULT_SONG = "default_song"
SILENT_SONG = "silent.mp3"  # Yes, this one has the extension and the other one does not. Don't ask why.
# YouTube API
API_KEY = get_api_key()
SEARCH_RESULT_LIMIT = 5
# RaspberryPi configuration
LED = 7
STOP_BUTTON = 13
REED_SWITCH = 15
# Time constants
INPUT_CHECK_INTERVAL = 0.1  # Time to wait before checking again if the switch is properly open
BLINK_DELAY = 0.2  # seconds delay between each blink when activating or deactivating pi
BLINK_TIMES = 3  # amount of times the led blinks when the circuit is activated
LONG_PRESS_TIME = 1  # amount of seconds the stop button needs to be pressed to toggle suspension
EXIT_HOUSE_TIMER = 30  # amount of seconds the user has to exit the house before the circuit activates again
# My speakers need to be kept alive because they turn off themselves if nothing is played for a while. Set this to
# None if you don't need this
KEEP_ALIVE_INTERVAL = 1 / SLEEP_SECONDS * 60 * 25
