import threading
from datetime import timedelta

from flask import Flask, render_template, request
import sys

from flask_jwt import JWT, jwt_required, current_identity

from LutraDB import database
from LutraDB.objects.position import Position
from LutraDB.objects.tracker import Tracker
from LutraDB.objects.user import User
from LutraDB.objects.user_tracker import UserTracker
from identity import Identity
from mqtt import LutraMQTT
import configparser



app = Flask(__name__)
app.config['JWT_AUTH_URL_RULE'] = '/api/v1/login'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
version = "0.0.1"

config = configparser.ConfigParser()
config.read('config.ini')
db_file = config['DB']['sqlite_file']
app.config['SECRET_KEY'] = config['App']['key']
mqtt = LutraMQTT(db_file, config['MQTT']['User'], config['MQTT']['Password'], config['MQTT']['Server'], int(config['MQTT']['Port']))
mqtt_thread = threading.Thread(target=mqtt.lutra_connect, args=[])
mqtt_thread.start()


@app.route("/")
def index():
    return render_template('index.html', version=version, maptiler_apikey=config["Maptiler"]["key"])


@app.route("/api/v1/track/<tracker_id>")
@jwt_required()
def track(tracker_id):
    db = database.LutraDB(db_file)
    tracker = Tracker(db)
    tracker.set_id(tracker_id)
    tracker.load_record()
    if UserTracker.check_authorization(db, current_identity, tracker):
        track = []
        positions = Position.get_last_day_for_tracker(db, tracker)
        last_added = False
        for position in positions:
            if len(track) == 0 or abs(track[-1]["lat"] - position.get_latitude()) > 0.0005 or abs(track[-1]["lng"] - position.get_longitude()) > 0.0005:
                track.append({
                    "lat": position.get_latitude(),
                    "lng": position.get_longitude(),
                    "ts": position.get_timestamp()
                })
                last_added = True
            else:
                last_added = False
        if not last_added:
            track.append({
                "lat": positions[-1].get_latitude(),
                "lng": positions[-1].get_longitude(),
                "ts": positions[-1].get_timestamp()
            })
        return track
    else:
        return "Not allowed."


@app.route('/api/v1/user')
@jwt_required()
def user():
    return {
        'name': current_identity.get_name()
    }


@app.route('/api/v1/trackers')
@jwt_required()
def trackers():
    db = database.LutraDB(db_file)
    tracker_data = {"trackers": []}
    trackers = UserTracker.get_trackers_by_user(db, current_identity)
    for tracker in trackers:
        position = Position.get_last_by_tracker(db, tracker)
        d = {
            "name": tracker.get_name(),
            "id": tracker.get_id()
        }
        if position is not None:
            d["lat"] = position.get_latitude()
            d["lng"] = position.get_longitude()
            d["ts"] = position.get_timestamp()
        tracker_data["trackers"].append(d)
    return tracker_data


@app.route('/api/v1/changepw', methods=["POST"])
@jwt_required()
def changepw():
    data = request.json
    user = current_identity

    if not 'oldpw' in data or not 'newpw' in data:
        return {
            "success": False
        }
    if not user.check_password(data['oldpw']):
        return {
            "success": False
        }
    user.hash_and_set_password(data['newpw'])
    user.save_record()
    return {
        "success": True
    }


def authenticate(username, password):
    db = database.LutraDB(db_file)
    user = User.get_by_username(db, username)
    if user is not None and user.check_password(password):
        identity = Identity(user.get_id())
        return identity


def identity(payload):
    db = database.LutraDB(db_file)
    user_id = payload['identity']
    user = User(db)
    user.set_id(user_id)
    user.load_record()
    return user


jwt = JWT(app, authenticate, identity)


if __name__ == '__main__':
    print('Please run Lutra using flask run.')
    sys.exit(1)
