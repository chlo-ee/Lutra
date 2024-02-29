from LutraDB.objects.db_object import DbObject, getter, setter


class Tracker(DbObject):
    def __init__(self, db):
        super().__init__(db)
        self._lutraDb_tableName = "Trackers"
        self.columns = ["ROWID", "Name", "TtnIdentifier", "LastSeen", "Voltage", "RSSI", "MinVoltage", "MaxVoltage", "MinRSSI", "MaxRSSI"]

    @staticmethod
    def get_all(db):
        t = Tracker(db)
        c = t._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(t.columns)} FROM Trackers")
        rows = c.fetchall()
        trackers = []
        for row in rows:
            tracker = Tracker(db)
            for n in range(len(t.columns)):
                tracker.values[tracker.columns[n]] = row[n]
            tracker.loaded = True
            tracker.is_new = False
            tracker.id = tracker.values["ROWID"]
            trackers.append(tracker)
        return trackers

    @staticmethod
    def get_by_ttn_identifier(db, identifier):
        tracker = Tracker(db)
        c = tracker._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(tracker.columns)} FROM Trackers WHERE TtnIdentifier = ?", [identifier])
        row = c.fetchone()
        if row is None:
            return None
        for n in range(len(tracker.columns)):
            tracker.values[tracker.columns[n]] = row[n]
        tracker.loaded = True
        tracker.is_new = False
        tracker.id = tracker.values["ROWID"]
        return tracker

    @getter
    def get_name(self):
        return self.values["Name"]

    @setter
    def set_name(self, name):
        self.values["Name"] = name

    @getter
    def get_ttn_identifier(self):
        return self.values["TtnIdentifier"]

    @setter
    def set_ttn_identifier(self, ttn_identifier):
        self.values["TtnIdentifier"] = ttn_identifier

    @getter
    def get_last_seen(self):
        return self.values["LastSeen"]

    @setter
    def set_last_seen(self, last_seen):
        self.values["LastSeen"] = last_seen

    @getter
    def get_voltage(self):
        return self.values["Voltage"]


    @setter
    def set_voltage(self, voltage):
        self.values["Voltage"] = voltage

    @getter
    def get_rssi(self):
        return self.values["RSSI"]

    @setter
    def set_rssi(self, rssi):
        self.values["RSSI"] = rssi

    @getter
    def get_min_voltage(self):
        return self.values["MinVoltage"]

    @setter
    def set_min_voltage(self, voltage):
        self.values["MinVoltage"] = voltage

    @getter
    def get_min_rssi(self):
        return self.values["MinRSSI"]

    @setter
    def set_min_rssi(self, rssi):
        self.values["MinRSSI"] = rssi

    @getter
    def get_max_voltage(self):
        return self.values["MaxVoltage"]

    @setter
    def set_max_voltage(self, voltage):
        self.values["MaxVoltage"] = voltage

    @getter
    def get_max_rssi(self):
        return self.values["MaxRSSI"]

    @setter
    def set_max_rssi(self, rssi):
        self.values["MaxRSSI"] = rssi
