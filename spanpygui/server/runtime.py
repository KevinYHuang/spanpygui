from time import time
from flask import Response, request, jsonify
import cv2

from spanpygui.server.app import route
from spanpygui.server.session import Session
from spanpygui.server.utils import increment_name

sessions: dict[str,Session] = {}

def new_session(name):
    s = Session(name=name, use_renderer=True)
    s.name = increment_name(s.name, sessions)
    sessions[s.name] = s
    return s


def generate_video(session: Session):
    while True:
        frame = session.player.get_curr_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@route('/<session_name>/video_feed')
def video_feed(session_name):
    if session_name not in sessions:
        return Response('Session not found', status=404)
    return Response(generate_video(sessions[session_name]),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@route('/<session_name>/player', methods=['POST', 'GET'])
def player_control(session_name):
    if session_name not in sessions:
        return Response('Session not found', status=404)

    if request.method == 'GET':
        return jsonify({
            'time': sessions[session_name].get_curr_time(), 
            'frame': sessions[session_name].get_curr_frame_num(),
            'duration': sessions[session_name].get_duration(),
            'playing': sessions[session_name].is_playing(),
        })
    elif request.method == 'POST':
        if 'time' in request.form:
            sessions[session_name].set_curr_time(float(request.form['time']))
        if 'play' in request.form:
            if int(request.form['play']):
                sessions[session_name].play()
            else:
                sessions[session_name].pause()

        return jsonify({
            'time': sessions[session_name].get_curr_time(), 
            'frame': sessions[session_name].get_curr_frame_num(),
            'duration': sessions[session_name].get_duration(),
            'playing': sessions[session_name].is_playing(),
        })

