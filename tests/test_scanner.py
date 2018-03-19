import json
import unittest

import time

from HomeTuner import scanner, setup_logging, init_assets

scanner.DATA = "tests/assets/data.json"


class AppTest(unittest.TestCase):
    A = 'aa:aa:aa:aa:aa:aa'
    B = 'bb:bb:bb:bb:bb:bb'

    @classmethod
    def setUpClass(cls):
        setup_logging(tofile=False)
        init_assets(folder="tests/assets/", overwrite=True)

    def setUp(self):
        pass

    def tearDown(self):
        with open(scanner.DATA, 'w') as f:
            json.dump({'last': '', 'visits': {}}, f)

    def test_no_new_device(self):
        scanner.save_newest_device(online_devices=[])
        with open(scanner.DATA) as f:
            after = json.load(f)
        self.assertEqual(after['visits'], {})

    def test_connected_device(self):
        scanner.save_newest_device(online_devices=[self.A])
        with open(scanner.DATA) as f:
            after = json.load(f)
        self.assertEqual(after['last'], self.A)
        self.assertEqual(list(after['visits'].keys()), [self.A])

    def test_disconnected_device(self):
        scanner.save_newest_device(online_devices=[self.A, self.B])
        with open(scanner.DATA, 'r+') as f:
            data = json.load(f)
            # update last seen property of B to be in the distant past. system should consider it as disconnected.
            data['visits'][self.B] = int(time.time() - scanner.LAST_SEEN_INTERVAL - 100)
            data['last'] = self.A
            f.seek(0)
            json.dump(data, f)
            f.truncate()
        scanner.save_newest_device(online_devices=[self.A, self.B])
        with open(scanner.DATA) as f:
            after = json.load(f)
        self.assertEqual(after['last'], self.B)  # B was disconnected, it should be now marked as the latest device

if __name__ == '__main__':
    unittest.main()
