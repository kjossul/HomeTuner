import json
import logging

from flask import Flask, Blueprint, render_template, request

from HomeTuner.util import file_handler, get_guest_mac

settings = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)


@settings.route('/settings', methods=['GET'])
def render_settings():
    mac = get_guest_mac()
    data = file_handler.read_data_file()
    return render_template('settings.html', name=data['devices'][mac]['name'], songs=data['devices'][mac]['songs'],
                           playing_order=data['devices'][mac]['playingOrder'], mac=mac)


@settings.route('/settings/<mac>', methods=['POST'])
def update_preferences(mac):
    data = file_handler.read_data_file()
    data['devices'][mac]['name'] = request.form['name']
    data['devices'][mac]['playingOrder'] = request.form['playingOrder']
    file_handler.write_data_file(data)
    logger.info("Updated {}'s preferences.".format(data['devices'][mac]['name']))
    return render_settings()