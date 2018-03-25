import json
import logging
import logging.config
import os
from shutil import copyfile
import time
from flask import Flask
from flask_bootstrap import Bootstrap
from HomeTuner.download import downloader
from config import SILENT_SONG, DATA_FILE, SONGS_DIR, DUMMY_MAC, DEFAULT_SONG
from HomeTuner.settings import settings
from HomeTuner.control import player

logger = logging.getLogger(__name__)


def setup_logging(path='logging.json', default_level=logging.INFO, env_key='LOG_CFG', tofile=True):
    """
    Setup logging configuration
    """
    path = path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
            if not tofile:
                config['root']['handlers'] = ['console']  # keeps only console
                config['handlers'] = {'console': config['handlers']['console']}
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def init_assets():
    if os.path.exists(SONGS_DIR):
        return
    else:
        os.makedirs(SONGS_DIR)
    with open(DATA_FILE, 'w+') as f:
        data = {'songs': {},
                'devices': {DUMMY_MAC: {"name": "admin",
                                        "songs": {},
                                        "lastVisit": int(time.time()),
                                        "playingOrder": "random"}}}
        json.dump(data, f)
        logger.info("Generated data file.")
        copyfile(DEFAULT_SONG + ".mp3", os.path.join(SONGS_DIR, DEFAULT_SONG + ".mp3"))
        copyfile(SILENT_SONG, os.path.join(SONGS_DIR, SILENT_SONG))
        logger.info("Copied default song and silent song to user directory.")


def create_app(config='config'):
    app = Flask(__name__)
    app.config.from_object(config)
    Bootstrap(app)
    app.register_blueprint(downloader)
    app.register_blueprint(settings)
    app.register_blueprint(player)
    return app
