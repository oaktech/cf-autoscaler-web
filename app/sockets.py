from flask import request
from flask.ext.socketio import join_room as _join_room
from flask.ext.socketio import leave_room as _leave_room

num_sockets = 0
room_members = {}


def get_num_sockets():
    global num_sockets
    return num_sockets


def get_socket_id():
    return request.sid


def connect_socket():
    global num_sockets
    num_sockets += 1


def disconnect_socket():
    import flask_socketio
    for room in flask_socketio.rooms():
        leave_room(room)

    global num_sockets
    print num_sockets
    if num_sockets == 0:
        raise Exception('Num sockets is already zero')
    num_sockets -= 1


def join_room(room_name):
    if room_name not in room_members:
        room_members[room_name] = 0
    room_members[room_name] += 1
    _join_room(room_name)


def leave_room(room_name):
    if room_name not in room_members:
        return
    if room_members[room_name] == 0:
        raise Exception('Num room members is already zero')
    room_members[room_name] -= 1
    _leave_room(room_name)


def rooms_with_members(match):
    return [room
            for room, count in room_members.items()
            if count > 0 and match in room]
