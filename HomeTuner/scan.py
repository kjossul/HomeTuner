import logging
import time
from config import LAST_SEEN_INTERVAL, SLEEP_SECONDS, REED_SWITCH, SILENT_SONG, KEEP_ALIVE_INTERVAL
from HomeTuner.util import file_handler
from HomeTuner.control import circuit
from HomeTuner.util import get_mac_addresses

logger = logging.getLogger(__name__)


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
                                       'lastVisit': 0,
                                       'nextSong': 'default_song'}
        logger.info("New devices added to file: {}".format(diff))
    last_seen = set(
        [device for device, v in data['devices'].items() if v['lastVisit'] + LAST_SEEN_INTERVAL > time.time()])
    diff = set(online_devices) - last_seen
    try:
        data['lastDevice'] = diff.pop()
        logger.info("Reconnected devices: {}.".format(diff | {data['lastDevice']}))
    except KeyError:
        pass
    for device in online_devices:
        data['devices'][device]['lastVisit'] = int(time.time())
    file_handler.write_data_file(data)


def main():
    logger.info("Launching scanner. Set to perform arp-scans every {} second(s)".format(SLEEP_SECONDS))
    if KEEP_ALIVE_INTERVAL:
        logger.info("Keeping speakers alive by playing silent mp3 every {} minute(s)"
                    .format(KEEP_ALIVE_INTERVAL * SLEEP_SECONDS / 60))
        counter = 0
    while True:
        if KEEP_ALIVE_INTERVAL:
            counter += 1
            counter %= KEEP_ALIVE_INTERVAL
            if counter == 0:
                circuit.play_music(song=SILENT_SONG, start=0)
            elif counter == 1:
                circuit.stop_music()

        save_newest_device()
        time.sleep(SLEEP_SECONDS)


if __name__ == '__main__':
    main()
