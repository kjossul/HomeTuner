import json
import logging

from flask import Flask, Blueprint, render_template, request, jsonify, Response
from googleapiclient.discovery import build
from HomeTuner.scanner import get_mac_addresses

logger = logging.getLogger(__name__)
# Flask
app = Flask(__name__)
downloader = Blueprint('downloader', __name__)


@downloader.route('/')
def home():
    mac = get_mac_addresses(hosts=request.remote_addr)
    return render_template('home.html', mac=mac)


@downloader.route('/search')
def search():
    return jsonify(youtube_search(request.args['k']))


@downloader.route('/video')
def video():
    return render_template('video.html', id=request.args['v'])


def get_api_key():
    with open(".apikey") as f:
        return f.read()


def youtube_search(keyword):
    logger.info("Searching youtube videos with key={}".format(keyword))
    youtube = build('youtube', 'v3', developerKey=get_api_key(), cache_discovery=False)
    search_response = youtube.search().list(
        q=keyword,
        part='id,snippet',
        maxResults=10,
        type='video'
    ).execute()
    return [{'thumbnail': result['snippet']['thumbnails']['default']['url'],
             'id': result['id']['videoId'],
             'title': result['snippet']['title']} for result in search_response.get('items', [])]
