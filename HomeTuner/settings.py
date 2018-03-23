import json
import logging

from flask import Flask, Blueprint, render_template, request

from config import SONGS
from HomeTuner.download import get_guest_mac

app = Flask(__name__)
settings = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)


@settings.route('/settings', methods=['GET'])
def render_settings():
    mac = get_guest_mac()
    with open(SONGS) as f:
        data = json.load(f)
    return render_template('settings.html', name=data['devices'][mac]['name'], songs=data['devices'][mac]['songs'],
                           playing_order=data['devices'][mac]['playingOrder'], mac=mac)


@settings.route('/settings/<mac>', methods=['POST'])
def update_preferences(mac):
    with open(SONGS, 'r+') as f:
        data = json.load(f)
        data['devices'][mac]['name'] = request.form['name']
        data['devices'][mac]['playingOrder'] = request.form['playingOrder']
        f.seek(0)
        json.dump(data, f)
        f.truncate()
        logger.info("Updated {}'s preferences.".format(data['devices'][mac]['name']))
    return render_settings()