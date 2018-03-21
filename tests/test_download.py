from HomeTuner import create_app, download
import unittest


class TestCase(unittest.TestCase):

    def setUpClass(cls):
        download.SONGS_DIR = "tests/Music"
        download.SONGS = "tests/songs.json"

    def setUp(self):
        app = create_app()
        app.testing = True
        self.app = app.test_client()

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
