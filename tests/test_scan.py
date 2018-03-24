import json
import logging
import unittest

import time

from HomeTuner import scan, setup_logging, util

util.DATA_FILE = "tests/data.json"


class AppTest(unittest.TestCase):
    A = 'aa:aa:aa:aa:aa:aa'
    B = 'bb:bb:bb:bb:bb:bb'
    BASE_DATA_FILE = {'last_device': '', 'devices': {}}
    logger = logging.getLogger(__name__)

    @classmethod
    def setUpClass(cls):
        setup_logging(tofile=False)
        util.file_handler.write_data_file(cls.BASE_DATA_FILE)

    def setUp(self):
        pass

    def tearDown(self):
        util.file_handler.write_data_file(self.BASE_DATA_FILE)

    def test_no_new_device(self):
        scan.save_newest_device(online_devices=[])
        after = util.file_handler.read_data_file()
        self.assertEqual(after['devices'], {})

    def test_connected_device(self):
        scan.save_newest_device(online_devices=[self.A])
        after = util.file_handler.read_data_file()
        self.assertEqual(after['last_device'], self.A)
        self.assertEqual(list(after['devices'].keys()), [self.A])

    def test_disconnected_device(self):
        scan.save_newest_device(online_devices=[self.A, self.B])
        data = util.file_handler.read_data_file()
        # update last seen property of B to be in the distant past. system should consider it as disconnected.
        data['devices'][self.B]['last_visit'] = int(time.time() - scan.LAST_SEEN_INTERVAL - 100)
        data['last_device'] = self.A
        util.file_handler.write_data_file(data)
        scan.save_newest_device(online_devices=[self.A, self.B])
        after = util.file_handler.read_data_file()
        self.assertEqual(after['last_device'], self.B)  # B was disconnected, it should be now marked as the latest device


if __name__ == '__main__':
    unittest.main()
