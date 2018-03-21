# Flask
DEBUG = True  # todo change debug to false when deploying
HOST = '0.0.0.0'
# Flask-Bootstrap
BOOTSTRAP_SERVE_LOCAL = True
# HomeTuner
import os
INTERFACE = "eno1"  # interface scanned by arp-scan
LAST_SEEN_INTERVAL = 300  # device is considered online if last connection was at most this amount of seconds ago
SLEEP_SECONDS = 1  # seconds between each arp-scan
DUMMY_MAC = "aa:aa:aa:aa:aa"  # fake MAC address for testing, etc
# Directories and generated files
DIRECTORY = os.path.expanduser('~/Documents/HomeTuner')
SONGS_DIR = os.path.join(DIRECTORY, 'Music')
DEVICES = os.path.join(DIRECTORY,"devices.json")
SONGS = os.path.join(DIRECTORY, "songs.json")
