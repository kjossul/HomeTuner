import json
import logging

import os
from re import findall

import youtube_dl
from flask import Flask, Blueprint, render_template, request, jsonify, abort
from urllib.parse import unquote_plus
from googleapiclient.discovery import build
from HomeTuner.scan import get_mac_addresses
from config import SONGS_DIR, DUMMY_MAC, API_KEY, SEARCH_RESULT_LIMIT, DEFAULT_SONG
from HomeTuner.util import file_handler

logger = logging.getLogger(__name__)
# Flask
app = Flask(__name__)
downloader = Blueprint('downloader', __name__)


@downloader.route('/')
def home():
    return render_template('home.html', name=get_guest_name())


def get_guest_mac():
    try:
        mac = get_mac_addresses(hosts=request.remote_addr)[0]
    except IndexError:
        mac = DUMMY_MAC
    return mac


@downloader.route('/search')
def search():
    mac = get_guest_mac()
    data = file_handler.read_data_file()
    if 'k' in request.args:
        videos = youtube_search(request.args['k'])
    else:
        videos = get_videos_duration(data['devices'][mac]['songs'].keys())
    for vid in videos:
        try:
            vid['saved'] = vid['id'] in data['devices'][mac]['songs']
            vid['savedStart'] = data['devices'][mac]['songs'][vid['id']]
        except KeyError:
            vid['saved'] = False
            vid['savedStart'] = 0
    return jsonify({'mac': mac, 'videos': videos})


@downloader.route('/songs/<song_id>')
def get_song(song_id):
    data = file_handler.read_data_file()
    try:
        return jsonify({'progress': data['songs'][song_id]['progress']})
    except KeyError:
        return jsonify({'progress': 0})


@downloader.route('/devices/<mac>/songs/', methods=['GET'])
def get_songs(mac):
    pass


@downloader.route('/devices/<mac>/songs/<song_id>', methods=['POST'])
def update_song(mac, song_id):
    post_data = request.get_json()
    mac = unquote_plus(mac)
    data = file_handler.read_data_file()
    data['devices'][mac]['songs'][song_id] = int(post_data['start'])
    data['lastDevice'] = mac
    file_handler.write_data_file(data)
    logger.info(
        "Updated song {} for user {} to start at {}".format(song_id, data['devices'][mac]['name'], post_data['start']))
    return jsonify({'start': post_data['start']}), 200, {'ContentType': 'application/json'}


@downloader.route('/devices/<mac>/songs/<song_id>', methods=['PUT'])
def put_song(mac, song_id):
    mac = unquote_plus(mac)
    ydl_opts = {'format': 'bestaudio/best',
                'outtmpl': '{}/%(id)s.%(ext)s'.format(SONGS_DIR),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'logger': logger,
                'progress_hooks': [manage_download]
                }
    data = file_handler.read_data_file()
    data['devices'][mac]['songs'][song_id] = 0  # initially sets song start time to 0
    data['devices'][mac]['nextSong'] = song_id
    data['lastDevice'] = mac
    download = True
    if song_id in data['songs'] and data['songs'][song_id]['progress'] == 100:
        logger.info("Song already downloaded. Adding to user rotation..")
        data['songs'][song_id]['savedBy'].append(mac)
        download = False
    else:
        data['songs'][song_id] = {'progress': 0, 'savedBy': [mac]}
    file_handler.write_data_file(data)
    if download:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            url = "https://www.youtube.com/watch?v=" + song_id
            ydl.download([url])
    return jsonify({'downloaded': download}), 200, {'ContentType': 'application/json'}


@downloader.route('/devices/<mac>/songs/<song_id>', methods=['DELETE'])
def remove_song(mac, song_id):
    mac = unquote_plus(mac)
    data = file_handler.read_data_file()
    del data['devices'][mac]['songs'][song_id]
    try:
        data['devices'][mac]['nextSong'] = list(data['devices'][mac]['songs'].keys())[0]
    except IndexError:
        data['devices'][mac]['nextSong'] = DEFAULT_SONG
    data['songs'][song_id]['savedBy'] = list(set(data['songs'][song_id]['savedBy']) - {mac})
    residual = data['songs'][song_id]['savedBy']
    if not residual:
        logger.info("Song {} is not used by any user. Deleting..".format(song_id))
        del data['songs'][song_id]
        os.remove(os.path.join(SONGS_DIR, song_id + ".mp3"))
    file_handler.write_data_file(data)
    return jsonify({'removedFromDisk': not residual}), 200, {'ContentType': 'application/json'}


def manage_download(info):
    data = file_handler.read_data_file()
    if info['status'] == 'error':
        logger.info("Error downloading: {}".format(info))
        # todo remove the song from info file
    else:
        filename = info['filename']
        song_id = filename[len(SONGS_DIR) + 1:filename.find('.')]
        try:
            if 'total_bytes' in info:
                total = info['total_bytes']
            else:
                total = info['total_bytes_estimate']
            data['songs'][song_id]['progress'] = info['downloaded_bytes'] / total * 100
        except (TypeError, KeyError):  # total_bytes not available
            data['songs'][song_id]['progress'] = 100 if info['status'] == 'finished' else 0
        file_handler.write_data_file(data)


def youtube_search(keyword):
    logger.info("Searching youtube videos with key={}".format(keyword))
    youtube = build('youtube', 'v3', developerKey=API_KEY, cache_discovery=False)
    search_response = youtube.search().list(
        q=keyword,
        part='id',
        maxResults=SEARCH_RESULT_LIMIT,
        type='video'
    ).execute()
    return get_videos_duration(result['id']['videoId'] for result in search_response.get('items', []))


def get_videos_duration(videos):
    youtube = build('youtube', 'v3', developerKey=API_KEY, cache_discovery=False)
    videos_response = youtube.videos().list(
        id=','.join(videos),
        part='contentDetails'
    ).execute()
    return [{'id': result['id'],
             'duration': iso8601_duration_as_seconds(result['contentDetails']['duration'])}
            for result in videos_response.get('items', [])]


def get_guest_name():
    mac = get_guest_mac()
    data = file_handler.read_data_file()
    return data['devices'][mac]['name']


def iso8601_duration_as_seconds(d):
    if d[0] != 'P':
        raise ValueError('Not an ISO 8601 Duration string')
    seconds = 0
    # split by the 'T'
    for i, item in enumerate(d.split('T')):
        for number, unit in findall('(?P<number>\d+)(?P<period>S|M|H|D|W|Y)', item):
            # print '%s -> %s %s' % (d, number, unit )
            number = int(number)
            this = 0
            if unit == 'Y':
                this = number * 31557600  # 365.25
            elif unit == 'W':
                this = number * 604800
            elif unit == 'D':
                this = number * 86400
            elif unit == 'H':
                this = number * 3600
            elif unit == 'M':
                # ambiguity ellivated with index i
                if i == 0:
                    this = number * 2678400  # assume 30 days
                    # print "MONTH!"
                else:
                    this = number * 60
            elif unit == 'S':
                this = number
            seconds = seconds + this
    return seconds
