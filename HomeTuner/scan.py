import json
import logging
import time
import re
import subprocess
from config import INTERFACE, LAST_SEEN_INTERVAL, SLEEP_SECONDS, DEVICES, SONGS

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
    try:
        with open(SONGS) as f:
            data = json.load(f)
        diff = set(online_devices) - set(data['devices'].keys())
        if diff:
            logger.info("Adding devices to songs file..")
            for device in diff:
                data['devices'][device] = {'name': device, 'songs': {}, 'playingOrder': 'random'}
            with open(SONGS, 'w') as f:
                json.dump(data, f)
        with open(DEVICES, 'r+') as f:
            data = json.load(f)
            last_seen = set(
                [device for device, visit in data['visits'].items() if visit + LAST_SEEN_INTERVAL > time.time()])
            diff = set(online_devices) - last_seen
            try:
                data['last'] = diff.pop()
                logger.info("New devices found: {}".format(diff))
            except KeyError:
                pass
            for device in online_devices:
                data['visits'][device] = int(time.time())
            f.seek(0)
            json.dump(data, f)
            f.truncate()
    except json.JSONDecodeError:
        pass


def main():
    logger.info("Launching scanner. Set to perform arp-scans every {} second(s)".format(SLEEP_SECONDS))
    while True:
        save_newest_device()
        time.sleep(SLEEP_SECONDS)


if __name__ == '__main__':
    main()
