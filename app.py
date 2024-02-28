import threading
from datetime import timedelta
from datetime import datetime
from datetime import timezone
from secrets import token_bytes

from flask import Flask, render_template, request, jsonify
import sys

from flask_jwt_extended import current_user
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies

from LutraDB import database
from LutraDB.objects.lutra_meta import LutraMeta
from LutraDB.objects.position import Position
from LutraDB.objects.tracker import Tracker
from LutraDB.objects.user import User
from LutraDB.objects.user_tracker import UserTracker
from mqtt import LutraMQTT
import configparser


version = "0.1.0"

config = configparser.ConfigParser()
config.read('config.ini')
db_file = config['DB']['sqlite_file']
db = database.LutraDB(db_file)
db.check_upgrades()


def init_jwt_secret():
    key = token_bytes(64)
    db = database.LutraDB(db_file)
    meta_object = LutraMeta(db)
    meta_object.set_key("JWT_SECRET")
    meta_object.set_value(key)
    meta_object.save_record()
    return key


jwt_secret = ""
if "JWT_SECRET" not in db.metadata:
    jwt_secret = init_jwt_secret()
else:
    jwt_secret = db.metadata["JWT_SECRET"]

app = Flask(__name__)
app.config['JWT_AUTH_URL_RULE'] = '/api/v1/login'
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config['JWT_SECRET_KEY'] = jwt_secret
app.config["JWT_COOKIE_SECURE"] = config['App']['production']

mqtt = LutraMQTT(db_file, config['MQTT']['User'], config['MQTT']['Password'], config['MQTT']['Server'], int(config['MQTT']['Port']))
mqtt_thread = threading.Thread(target=mqtt.lutra_connect, args=[])
mqtt_thread.start()

jwt = JWTManager(app)


@app.route("/")
def index():
    return render_template('index.html', version=version, maptiler_apikey=config["Maptiler"]["key"])


@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=current_user)
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response


@app.route("/api/v1/track/<tracker_id>")
@jwt_required()
def track(tracker_id):
    db = database.LutraDB(db_file)
    tracker = Tracker(db)
    tracker.set_id(tracker_id)
    tracker.load_record()
    if UserTracker.check_authorization(db, current_user, tracker):
        t = []
        positions = Position.get_last_day_for_tracker(db, tracker)
        last_added = False
        for position in positions:
            if len(t) == 0 or abs(t[-1]["lat"] - position.get_latitude()) > 0.0005 or abs(t[-1]["lng"] - position.get_longitude()) > 0.0005:
                t.append({
                    "lat": position.get_latitude(),
                    "lng": position.get_longitude(),
                    "ts": position.get_timestamp()
                })
                last_added = True
            else:
                last_added = False
        if not last_added:
            t.append({
                "lat": positions[-1].get_latitude(),
                "lng": positions[-1].get_longitude(),
                "ts": positions[-1].get_timestamp()
            })
        return t
    else:
        return "Not allowed."


@app.route('/api/v1/user')
@jwt_required()
def userdata():
    return {
        'name': current_user.get_name()
    }


@app.route('/api/v1/trackers')
@jwt_required()
def trackers():
    db = database.LutraDB(db_file)
    tracker_data = {"trackers": []}
    for tracker in UserTracker.get_trackers_by_user(db, current_user):
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


@app.route('/api/v1/change_pw', methods=["POST"])
@jwt_required()
def change_pw():
    data = request.json
    user = current_user

    if 'oldpw' not in data or 'newpw' not in data:
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


@app.route("/api/v1/login", methods=["POST"])
def authenticate():
    username = request.json.get("username")
    password = request.json.get("password")

    if username is None or password is None:
        return {'success': False}, 401
    db = database.LutraDB(db_file)
    user = User.get_by_username(db, username)
    if user.check_password(password):
        response = jsonify({'success': True})
        access_token = create_access_token(identity=user)
        set_access_cookies(response, access_token)
        return response
    return {'success': False}, 401


@app.route("/api/v1/logout", methods=["POST"])
def logout():
    response = jsonify({"success": True})
    unset_jwt_cookies(response)
    return response


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.get_id()


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    db = database.LutraDB(db_file)
    user_id = jwt_data["sub"]
    user = User(db)
    user.set_id(user_id)
    user.load_record()
    return user


if __name__ == '__main__':
    print('Please run Lutra using flask run.')
    sys.exit(1)
