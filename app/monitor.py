from __future__ import print_function
from functools import wraps
from flask import request
from app import config
from flask.ext.socketio import disconnect
from app import socketio
from app import util
from models import App
from models import AppStats
import helpers
import sockets

namespace = '/monitor/stats'
error_namespace = '/errors'
track_stats = False


def require_login(func):
    @wraps(func)
    def wrapped_f(*args):
        sockets.connect_socket()
        if not helpers.is_logged_in():
            return disconnect()
        return func(*args)
    return wrapped_f


@socketio.on('connect', namespace=namespace)
@require_login
def on_connect():
    """Verifies that the user is logged in and that the app they want to monitor
    exists. Joins them to a "room" for that app. Emits an event containing a
    history of activity for the past 900 seconds. Starts polling for real time
    stats on the app's performance.
    """

    print('connecting')
    app_id = request.args.get('app_id', None)
    if not app_id:
        print ('app_id is required')
        return disconnect()
    app = App.find_by_id(app_id)
    if not app:
        print ('app not found')
        return disconnect()

    print ('watching app', app_id)
    sockets.join_room(get_app_room_id(app_id))

    interval = request.args.get('history_interval', 900)
    app_stats = AppStats.get_history(app_id, interval=interval)
    socketio.emit('history', util.to_dict(app_stats),
                  room=request.sid, namespace=namespace)

    resume_stats()


@socketio.on('disconnect', namespace=namespace)
def on_disconnect():
    """Unregister's user from the app's monitoring "room".
    """
    print ('disconnecting', request.sid)
    sockets.disconnect_socket()
    pause_stats()


@socketio.on('connect', namespace=error_namespace)
@require_login
def on_error_connect():
    pass


def pause_stats():
    """Checks if there are any sockets monitoring any apps. If nobody is
    monitoring, then set the flag to stop monitoring.
    """
    if sockets.get_num_sockets() == 0:
        global track_stats
        track_stats = False


def resume_stats():
    """Sets the flag to start monitoring apps.
    """
    global track_stats
    track_stats = True


def get_app_room_id(app_id):
    """Creates a room id from an app_id
    """
    return 'apps/' + app_id


def update_app_watchers(app_id, event, data):
    """Sends a dict of data to all sockets monitoring app_id.

    Args:
        app_id (str): Cloud Foundry app guid
        event (str): Event name
        data (dict): Event data
    """
    return socketio.emit(
        event, data, room=get_app_room_id(app_id), namespace=namespace)


def send_stats():
    """Runs forever in a socket.io background task and sends updates on all
    monitored apps. Updates are checked and sent on the configured interval
    `scaling.monitor_interval`.
    """
    while True:
        global track_stats
        if track_stats:
            try:
                apps = sockets.rooms_with_members('apps/')
                print ('getting stats for apps', apps)
                for room in apps:
                    app_id = room.split('/')[-1]
                    try:
                        app = App.find_by_id(app_id)
                        stats = app.get_current_stats(
                            include_instance_stats=True)
                        update_app_watchers(app_id, 'stats',
                                                    stats.to_dict())
                    except Exception as e:
                        import traceback
                        print(traceback.format_exc())
                        print(type(e), e.message)

            except Exception as e:
                print (e)
        # else:
            # print ('No clients active, sleeping.')

        socketio.sleep(config.scaling_monitor_interval)


socketio.start_background_task(target=send_stats)
