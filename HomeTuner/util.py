import json
import logging
import re
import subprocess
import threading

from flask import request

from config import DATA_FILE, DUMMY_MAC, INTERFACE

logger = logging.getLogger(__name__)


class FileHandler:
    def __init__(self):
        self._lock = threading.Lock()

    def read_data_file(self):
        self._lock.acquire()
        with open(DATA_FILE) as f:
            data = json.load(f)
        self._lock.release()
        return data

    def write_data_file(self, data):
        self._lock.acquire()
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
        self._lock.release()


file_handler = FileHandler()


def get_guest_name():
    mac = get_guest_mac()
    data = file_handler.read_data_file()
    return data['devices'][mac]['name']


def get_guest_mac():
    try:
        mac = get_mac_addresses(hosts=request.remote_addr)[0]
    except IndexError:
        mac = DUMMY_MAC
    return mac


def get_hosts():
    return " ".join("192.168.1.{}".format(i) for i in range(200, 255))


def get_mac_addresses(hosts=get_hosts()):
    p = subprocess.Popen("arp-scan --interface={} {} -q -g".format(INTERFACE, hosts), shell=True,
                         stdout=subprocess.PIPE)
    arp_scan, err = p.communicate()
    return re.findall('(?:[0-9a-fA-F]:?){12}', str(arp_scan))