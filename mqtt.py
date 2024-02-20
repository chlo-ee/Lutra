import base64
import json
import random
import time
from time import sleep

from paho.mqtt import client as mqtt_client

from LutraDB.database import LutraDB
from LutraDB.objects.position import Position
from LutraDB.objects.tracker import Tracker


class LutraMQTT(mqtt_client.Client):
    def __init__(self, db_file, username, password, broker, port):
        super().__init__(f'lutra-srv-{random.randint(0, 1000)}')
        self.broker = broker
        self.port = port
        self.db_file = db_file
        self.db = None
        self.username = username
        self.username_pw_set(username, password)
        self.on_connect = LutraMQTT.lutra_on_connect
        self.on_disconnect = LutraMQTT.lutra_on_disconnect
        self.on_message = LutraMQTT.lutra_on_message

    def lutra_connect(self):
        self.db = LutraDB(self.db_file)
        print("[MQTT] Connecting...")
        self.connect(self.broker, self.port)
        self.loop_forever()

    def subscribe_to_all_trackers(self):
        trackers = Tracker.get_all(self.db)
        for tracker in trackers:
            topic = f"v3/{self.username}/devices/{tracker.get_ttn_identifier()}/up"
            print(f"Subscribing to {topic}")
            self.subscribe(topic)

    @staticmethod
    def lutra_on_message(client, userdata, msg):
        decoded_payload = msg.payload.decode()
        print(f"Received '{decoded_payload}' from '{msg.topic}' topic")
        parsed = json.loads(decoded_payload)
        if 'end_device_ids' not in parsed:
            return
        if 'device_id' not in parsed['end_device_ids']:
            return
        dev_id = parsed['end_device_ids']['device_id']
        if 'uplink_message' not in parsed:
            return
        if 'frm_payload' not in parsed['uplink_message']:
            return
        payload = parsed['uplink_message']['frm_payload']
        decoded = base64.b64decode(payload)
        lat = (decoded[0] + (decoded[1] << 8) + (decoded[2] << 16) + (decoded[3] << 24)) / 10000
        lng = (decoded[4] + (decoded[5] << 8) + (decoded[6] << 16) + (decoded[7] << 24)) / 10000
        tracker = Tracker.get_by_ttn_identifier(client.db, dev_id)
        position = Position(client.db)
        position.set_tracker_id(tracker.get_id())
        position.set_timestamp(time.time())
        position.set_latitude(lat)
        position.set_longitude(lng)
        position.save_record()

    @staticmethod
    def lutra_on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Connected.")
            client.subscribe_to_all_trackers()
        else:
            print(f"[MQTT] Connection failed. Code {rc}")
            sleep(10)
            print("[MQTT] Retrying...")
            client.connect(client.broker, client.port)

    @staticmethod
    def lutra_on_disconnect(client, userdata, rc):
        print("[MQTT] Disconnected.")
        sleep(10)
        no_net = True
        while no_net:
            try:
                print("[MQTT] Connecting...")
                client.connect(client.broker, client.port)
                no_net = False
            except:
                print("[MQTT] Network unavailable")
                sleep(10)
