import json
import logging

import os
from re import findall

import youtube_dl
from flask import Flask, Blueprint, render_template, request, jsonify, abort
from urllib.parse import unquote_plus
from googleapiclient.discovery import build
from HomeTuner.scan import get_mac_addresses
from config import SONGS, SONGS_DIR, DUMMY_MAC

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
    with open(SONGS) as f:
        data = json.load(f)
        if 'k' in request.args:
            videos = youtube_search(request.args['k'])
        else:
            videos = [{'id': song_id} for song_id in data['devices'][mac]['songs']]
            logger.info(videos, data['devices'][mac])
        for vid in videos:
            try:
                vid['saved'] = vid['id'] in data['devices'][mac]['songs']
            except KeyError:
                vid['saved'] = False
    return jsonify({'mac': mac, 'videos': videos})


@downloader.route('/songs/<song_id>')
def get_song(song_id):
    with open(SONGS) as f:
        songs = json.load(f)
    try:
        return jsonify({'progress': songs['songs'][song_id]['progress']})
    except KeyError:
        return jsonify({'progress': 0})


@downloader.route('/devices/<mac>/songs/', methods=['GET'])
def get_songs(mac):
    pass


@downloader.route('/devices/<mac>/songs/<song_id>', methods=['PUT'])
def put_song(mac, song_id):
    mac = unquote_plus(mac)
    logger.info("{} requesting to add {} to his songs".format(mac, song_id))
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
    with open(SONGS) as f:
        songs = json.load(f)
    songs['devices'][mac]['songs'][song_id] = 0  # initially sets song start time to 0
    download = True
    if song_id in songs['songs'] and songs['songs'][song_id]['progress'] == 100:
        logger.info("Song already downloaded. Adding to user rotation..")
        songs['songs'][song_id]['savedBy'].append(mac)
        download = False
    else:
        songs['songs'][song_id] = {'progress': 0, 'savedBy': [mac]}
    with open(SONGS, 'w') as f:
        json.dump(songs, f)
    if download:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            url = "https://www.youtube.com/watch?v=" + song_id
            ydl.download([url])
    return jsonify({'downloaded': download}), 200, {'ContentType': 'application/json'}


@downloader.route('/devices/<mac>/songs/<song_id>', methods=['DELETE'])
def remove_song(mac, song_id):
    mac = unquote_plus(mac)
    with open(SONGS) as f:
        data = json.load(f)
    del data['devices'][mac]['songs'][song_id]
    data['songs'][song_id]['savedBy'] = list(set(data['songs'][song_id]['savedBy']) - {mac})
    residual = data['songs'][song_id]['savedBy']
    if not residual:
        logger.info("Song {} is not used by any user. Deleting..".format(song_id))
        del data['songs'][song_id]
        os.remove(os.path.join(SONGS_DIR, song_id + ".mp3"))
    with open(SONGS, 'w') as f:
        json.dump(data, f)
    return jsonify({'removedFromDisk': not residual}), 200, {'ContentType': 'application/json'}


def manage_download(info):
    with open(SONGS) as f:
        songs = json.load(f)
    if info['status'] == 'error':
        logger.info("Error downloading: {}".format(info))
        # todo remove the song from info file
    else:
        filename = info['filename']
        id = filename[len(SONGS_DIR) + 1:filename.find('.')]
        try:
            if 'total_bytes' in info:
                total = info['total_bytes']
            else:
                total = info['total_bytes_estimate']
            songs['songs'][id]['progress'] = info['downloaded_bytes'] / total * 100
        except (TypeError, KeyError):  # total_bytes not available
            songs['songs'][id]['progress'] = 100 if info['status'] == 'finished' else 0
        with open(SONGS, 'w') as f:
            json.dump(songs, f)


def get_api_key():
    with open(".apikey") as f:
        return f.read()


def youtube_search(keyword):
    logger.info("Searching youtube videos with key={}".format(keyword))
    youtube = build('youtube', 'v3', developerKey=get_api_key(), cache_discovery=False)
    search_response = youtube.search().list(
        q=keyword,
        part='id',
        maxResults=5,
        type='video'
    ).execute()
    search_response = youtube.videos().list(
        id=','.join(result['id']['videoId'] for result in search_response.get('items', [])),
        part='contentDetails'
    ).execute()
    return [{'id': result['id'],
             'duration': iso8601_duration_as_seconds(result['contentDetails']['duration'])}
            for result in search_response.get('items', [])]


def get_guest_name():
    mac = get_guest_mac()
    with open(SONGS) as f:
        data = json.load(f)
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
