import os, sys
import subprocess
import thread
import wx
import time
import re
import uuid
import platform
import inspect
import struct
import time
from game import Game
import startgame
from flask import Flask, render_template, session, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import thread
import eventlet
eventlet.monkey_patch()

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Serve up JS + sprites
@app.route('/<path:path>')
def send_js(path):
    return send_from_directory(app.static_folder, path)

@app.route('/')
def index():
    return render_template('myhtml.html')

# -------------------------------- #
#  query handlers                  #
# -------------------------------- #

#TODO: return name of city OR person
@socketio.on('get_random_person', namespace='/gameplay')
def send_random_person(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('return info',
        {'data': str(startgame.random_p), 'count': session['receive_count']})

@socketio.on('get_city_name', namespace='/gameplay')
def send_city_name(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('return info',
        {'data': str(startgame.city_name), 'count': session['receive_count']})

@socketio.on('get_lot_json', namespace='/gameplay')
def send_lot_json(message):
    emit('return lots',
         {'data': startgame.json_lot_type_dict, 'count': session['receive_count']})

@socketio.on('get_street_json', namespace='/gameplay')
def send_street_json(message):
    emit('return streets',
         {'data': startgame.json_street_type_dict, 'count': session['receive_count']})


@socketio.on('ready', namespace='/gameplay')
def ready():
    emit('ready response',
         {'data': str(startgame.ready), 'count': 000})

thread.start_new_thread(startgame.game_start,())
socketio.run(app)