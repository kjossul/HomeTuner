from flask import Flask, Blueprint, render_template

app = Flask(__name__)
settings = Blueprint('settings', __name__)


@settings.route('/settings')
def render_settings():
    return render_template('settings.html')
