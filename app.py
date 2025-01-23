from flask import Flask, request
from flask_socketio import SocketIO, emit

import random
import string

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}  # To store user IDs and random assigned IDs

def generate_random_id(length=8):
    """Generate a random ID for users."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/')
def index():
    return "Flask Video Call Backend Running"

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    random_id = generate_random_id()
    users[sid] = {'id': random_id, 'in_call': False}
    emit('update_users', {sid: users[sid] for sid in users}, broadcast=True)
    print(f"User connected: {random_id}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in users:
        if users[sid]['in_call']:
            # Notify the other user in the call
            emit('call_ended', {'message': 'User disconnected'}, broadcast=True)
        users.pop(sid, None)
        emit('update_users', {sid: users[sid] for sid in users}, broadcast=True)
        print(f"User disconnected: {sid}")

@socketio.on('call_request')
def handle_call_request(data):
    from_user = request.sid
    to_user = data.get('to')
    if to_user in users and not users[to_user]['in_call']:
        emit('call_received', {'from': users[from_user]['id'], 'sid': from_user}, to=to_user)
    else:
        emit('call_failed', {'message': 'User is unavailable'}, to=from_user)

@socketio.on('accept_call')
def handle_accept_call(data):
    from_user = request.sid
    to_user = data.get('to')
    if to_user in users and not users[to_user]['in_call']:
        users[from_user]['in_call'] = True
        users[to_user]['in_call'] = True
        emit('call_accepted', {'from': users[from_user]['id']}, to=to_user)
        print(f"Call accepted between {from_user} and {to_user}")
    else:
        emit('call_failed', {'message': 'User is unavailable'}, to=from_user)

@socketio.on('reject_call')
def handle_reject_call(data):
    from_user = request.sid
    to_user = data.get('to')
    if to_user in users:
        emit('call_rejected', {'message': 'User rejected the call'}, to=to_user)
        print(f"Call rejected by {from_user} for {to_user}")

@socketio.on('offer')
def handle_offer(data):
    to_user = data.get('to')
    emit('offer', {'offer': data.get('offer'), 'from': request.sid}, to=to_user)

@socketio.on('answer')
def handle_answer(data):
    to_user = data.get('to')
    emit('answer', {'answer': data.get('answer')}, to=to_user)

@socketio.on('candidate')
def handle_candidate(data):
    to_user = data.get('to')
    emit('candidate', {'candidate': data.get('candidate')}, to=to_user)

@socketio.on('end_call')
def handle_end_call(data):
    from_user = request.sid
    to_user = data.get('to')
    if to_user in users:
        users[from_user]['in_call'] = False
        users[to_user]['in_call'] = False
        emit('call_ended', {'message': 'Call has ended'}, to=to_user)
        emit('call_ended', {'message': 'Call has ended'}, to=from_user)
        print(f"Call ended between {from_user} and {to_user}")

if __name__ == '__main__':
    socketio.run(app, debug=False)
