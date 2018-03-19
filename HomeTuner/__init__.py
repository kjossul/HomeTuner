import json
import logging
import logging.config
import os

ASSETS_FOLDER = "HomeTuner/assets/"
DATA = ASSETS_FOLDER + "data.json"

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


def init_assets(folder=ASSETS_FOLDER, overwrite=False):
    data = {'devices': {}, 'last': ""}
    if os.path.exists(folder) and not overwrite:
        return
    directory = "{}/{}".format(os.getcwd(),folder)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(directory + "data.json", 'w+') as f:
        logger.info("Generating files..")
        json.dump(data, f)
