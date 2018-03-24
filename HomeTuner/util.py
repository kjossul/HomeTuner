import json
import logging
import threading
from config import DATA_FILE

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
