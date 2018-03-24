import json
import logging
import time
import re
import subprocess
from config import INTERFACE, LAST_SEEN_INTERVAL, SLEEP_SECONDS
from HomeTuner.util import file_handler

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
    data = file_handler.read_data_file()
    diff = set(online_devices) - set(data['devices'].keys())
    if diff:
        for device in diff:
            data['devices'][device] = {'name': device,
                                       'songs': {},
                                       'playingOrder': 'random',
                                       'last_visit': 0,
                                       'next_song': 'default_song.mp3'}
        logger.info("New devices added to file: {}".format(diff))
    last_seen = set(
        [device for device, v in data['devices'].items() if v['last_visit'] + LAST_SEEN_INTERVAL > time.time()])
    diff = set(online_devices) - last_seen
    try:
        data['last_device'] = diff.pop()
        logger.info("Reconnected devices: {}.".format(diff | {data['last_device']}))
    except KeyError:
        pass
    for device in online_devices:
        data['devices'][device]['last_visit'] = int(time.time())
    file_handler.write_data_file(data)


def main():
    logger.info("Launching scanner. Set to perform arp-scans every {} second(s)".format(SLEEP_SECONDS))
    while True:
        save_newest_device()
        time.sleep(SLEEP_SECONDS)


if __name__ == '__main__':
    main()
