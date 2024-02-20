import threading

from flask import Flask, render_template
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
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_AUTH_URL_RULE'] = '/api/v1/login'
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
    return render_template('index.html', version=version, username="RawBin", maptiler_apikey=config["Maptiler"]["key"])


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
        for position in positions:
            if len(track) == 0 or abs(track[-1]["lat"] - position.get_latitude()) > 0.0005 or abs(track[-1]["lng"] - position.get_longitude()) > 0.0005:
                track.append({
                    "lat": position.get_latitude(),
                    "lng": position.get_longitude(),
                    "ts": position.get_timestamp()
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

def authenticate(username, password):
    db = database.LutraDB(db_file)
    user = User.get_by_username(db, username)
    if user is not None and user.get_password() == password:
        identity = Identity(user.get_id())
        return identity


def identity(payload):
    db = database.LutraDB(db_file)
    print(payload)
    user_id = payload['identity']
    user = User(db)
    user.set_id(user_id)
    user.load_record()
    return user


jwt = JWT(app, authenticate, identity)


if __name__ == '__main__':
    print('Please run Lutra using flask run.')
    sys.exit(1)
