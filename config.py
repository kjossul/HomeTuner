# Flask
DEBUG = True  # todo change debug to false when deploying
HOST = '0.0.0.0'
# Flask-Bootstrap
BOOTSTRAP_SERVE_LOCAL = True
# HomeTuner
INTERFACE = "eno1"  # interface scanned by arp-scan
LAST_SEEN_INTERVAL = 300  # device is considered online if last connection was at most this amount of seconds ago
SLEEP_SECONDS = 1  # seconds between each arp-scan
DATA = "HomeTuner/data.json"
