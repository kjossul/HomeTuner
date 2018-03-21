import json
import logging
import logging.config
import os

from flask import Flask
from flask_bootstrap import Bootstrap
from HomeTuner.downloader import downloader

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


def init_assets(folder="HomeTuner/", overwrite=False):
    data = {'visits': {}, 'last': ""}
    if not overwrite:
        return
    with open(folder+"data.json", 'w+') as f:
        logger.info("Generating data file")
        json.dump(data, f)


def create_app(config='config'):
    app = Flask(__name__)
    app.config.from_object(config)
    Bootstrap(app)
    app.register_blueprint(downloader)
    return app