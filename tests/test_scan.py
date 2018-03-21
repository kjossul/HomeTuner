import json
import unittest

import time

from HomeTuner import scan, setup_logging, init_assets

scan.DEVICES = "tests/devices.json"


class AppTest(unittest.TestCase):
    A = 'aa:aa:aa:aa:aa:aa'
    B = 'bb:bb:bb:bb:bb:bb'

    @classmethod
    def setUpClass(cls):
        setup_logging(tofile=False)

    def setUp(self):
        pass

    def tearDown(self):
        with open(scan.DEVICES, 'w') as f:
            json.dump({'last': '', 'visits': {}}, f)

    def test_no_new_device(self):
        scan.save_newest_device(online_devices=[])
        with open(scan.DEVICES) as f:
            after = json.load(f)
        self.assertEqual(after['visits'], {})

    def test_connected_device(self):
        scan.save_newest_device(online_devices=[self.A])
        with open(scan.DEVICES) as f:
            after = json.load(f)
        self.assertEqual(after['last'], self.A)
        self.assertEqual(list(after['visits'].keys()), [self.A])

    def test_disconnected_device(self):
        scan.save_newest_device(online_devices=[self.A, self.B])
        with open(scan.DEVICES, 'r+') as f:
            data = json.load(f)
            # update last seen property of B to be in the distant past. system should consider it as disconnected.
            data['visits'][self.B] = int(time.time() - scan.LAST_SEEN_INTERVAL - 100)
            data['last'] = self.A
            f.seek(0)
            json.dump(data, f)
            f.truncate()
        scan.save_newest_device(online_devices=[self.A, self.B])
        with open(scan.DEVICES) as f:
            after = json.load(f)
        self.assertEqual(after['last'], self.B)  # B was disconnected, it should be now marked as the latest device

if __name__ == '__main__':
    unittest.main()
