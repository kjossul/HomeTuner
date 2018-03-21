import json
import logging
import time
import re
import subprocess
from config import INTERFACE, LAST_SEEN_INTERVAL, SLEEP_SECONDS, DATA

logger = logging.getLogger(__name__)


def get_hosts():
    return " ".join("192.168.1.{}".format(i) for i in range(200, 255))


def get_mac_addresses(hosts=get_hosts()):
    p = subprocess.Popen("arp-scan --interface={} {} -q -g".format(INTERFACE, hosts), shell=True,
                         stdout=subprocess.PIPE)
    arp_scan, err = p.communicate()
    return re.findall('(?:[0-9a-fA-F]:?){12}', str(arp_scan))


def save_newest_device(online_devices=None):
    """
    Updates data file with mac address of the newest device added to the network
    """
    if online_devices is None:
        online_devices = get_mac_addresses()
    with open(DATA) as f:
        data = json.load(f)
        last_seen = set(
            [device for device, visit in data['visits'].items() if visit + LAST_SEEN_INTERVAL > time.time()])
        diff = set(online_devices) - last_seen
        try:
            data['last'] = diff.pop()
            logger.info("New device found! Mac address: {}".format(data['last']))
        except KeyError:
            pass
    with open(DATA, 'w') as f:
        for device in online_devices:
            data['visits'][device] = int(time.time())
        json.dump(data, f)


def main():
    while True:
        save_newest_device()
        time.sleep(SLEEP_SECONDS)


if __name__ == '__main__':
    main()
