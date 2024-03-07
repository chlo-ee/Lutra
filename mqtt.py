import base64
import json
import random
import time
from time import sleep

from paho.mqtt import client as mqtt_client

from LutraDB.database import LutraDB
from LutraDB.objects.position import Position
from LutraDB.objects.tracker import Tracker

packet_type_gps = 1
packet_type_status = 2

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
            print(f"[MQTT] Subscribing to {topic}")
            self.subscribe(topic)

    @staticmethod
    def lutra_on_message(client, userdata, msg):
        decoded_payload = msg.payload.decode()
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
        if 'rx_metadata' not in parsed['uplink_message']:
            return

        tracker = Tracker.get_by_ttn_identifier(client.db, dev_id)
        if not tracker:
            return
        payload = parsed['uplink_message']['frm_payload']
        decoded = base64.b64decode(payload)

        rssi = -1000
        gateway_location = None
        for gateway in parsed['uplink_message']['rx_metadata']:
            if 'rssi' in gateway:
                if gateway['rssi'] > rssi:
                    rssi = gateway['rssi']
                    if 'location' in gateway:
                        gateway_location = gateway["location"]

        if decoded[0] >> 4 == packet_type_gps:
            lat = (decoded[1] + (decoded[2] << 8) + (decoded[3] << 16) + (decoded[4] << 24)) / 10000
            lng = (decoded[5] + (decoded[6] << 8) + (decoded[7] << 16) + (decoded[8] << 24)) / 10000
            hdop = decoded[9]
            sats = decoded[10]
            print(f"[MQTT] Received ({lat},{lng}; hdop={hdop}; sats={sats}) from {dev_id} - RSSI: {rssi}db")
            position = Position(client.db)
            position.set_tracker_id(tracker.get_id())
            position.set_timestamp(time.time())
            position.set_latitude(lat)
            position.set_longitude(lng)
            position.set_source("GPS")
            position.save_record()
        elif decoded[0] >> 4 == packet_type_status:
            voltage = int(decoded[1] + (decoded[2] << 8))
            print(f"[MQTT] Received Bat={voltage} from {dev_id} - RSSI: {rssi}db")
            tracker.set_voltage(voltage)
            if tracker.get_min_voltage() is None or voltage < int(tracker.get_min_voltage()):
                tracker.set_min_voltage(voltage)
            if tracker.get_max_voltage() is None or voltage > int(tracker.get_max_voltage()):
                tracker.set_max_voltage(voltage)
            last_position = Position.get_last_by_tracker(client.db, tracker)
            if rssi >= -70 and gateway_location and (not last_position or (last_position.get_source() == "GW" or last_position.get_timestamp() < time.time() - 1200)):
                position = Position(client.db)
                position.set_tracker_id(tracker.get_id())
                position.set_timestamp(time.time())
                position.set_latitude(gateway_location["latitude"])
                position.set_longitude(gateway_location["longitude"])
                position.set_source("GW")
                position.save_record()

        tracker.set_rssi(rssi)
        if tracker.get_min_rssi() is None or rssi < int(tracker.get_min_rssi()):
            tracker.set_min_rssi(rssi)
        if tracker.get_max_rssi() is None or rssi > int(tracker.get_max_rssi()):
            tracker.set_max_rssi(rssi)
        tracker.set_last_seen(time.time())
        tracker.save_record()

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
