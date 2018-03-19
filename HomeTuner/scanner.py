import json
import logging
import time
import re
import subprocess
from . import DATA

INTERFACE = "eno1"
LAST_SEEN_INTERVAL = 300  # device is considered to online if last connection was at most this amount of secs ago

logger = logging.getLogger(__name__)


def get_online_devices():
    hosts = " ".join("192.168.1.{}".format(i) for i in range(200, 255))
    p = subprocess.Popen("arp-scan --interface={} {} -q -g".format(INTERFACE, hosts), shell=True,
                         stdout=subprocess.PIPE)
    arp_scan, err = p.communicate()
    return re.findall('(?:[0-9a-fA-F]:?){12}', arp_scan)


def save_newest_device(online_devices=None):
    """
    Updates data file with mac address of the newest device added to the network
    """
    if online_devices is None:
        online_devices = get_online_devices()
    with open(DATA) as f:
        data = json.load(f)
        last_seen = set([device for device, v in data['devices'].items() if
                         v.get('last_online', time.time()) + LAST_SEEN_INTERVAL > time.time()])
        diff = set(online_devices) - last_seen
        try:
            data['last'] = diff.pop()
            logger.info("New device found! Mac address: {}".format(data['last']))
        except KeyError:
            pass
    with open(DATA, 'w') as f:
        for device in online_devices:
            if device not in data['devices']:
                data['devices'][device] = {}
            data['devices'][device]['last_online'] = int(time.time())
        json.dump(data, f)


def main():
    while True:
        save_newest_device()
        time.sleep(1)


if __name__ == '__main__':
    main()
