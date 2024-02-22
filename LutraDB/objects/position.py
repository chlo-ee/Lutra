import time

from LutraDB.objects.db_object import DbObject, getter, setter
from LutraDB.objects.tracker import Tracker


class Position(DbObject):
    def __init__(self, db):
        super().__init__(db)
        self._lutraDb_tableName = "Positions"
        self.columns = ["ROWID", "TrackerID", "Timestamp", "Latitude", "Longitude"]

    @staticmethod
    def get_last_by_tracker(db, tracker: Tracker):
        position = Position(db)
        c = position._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(position.columns)} FROM Positions WHERE TrackerID=? ORDER BY Timestamp DESC LIMIT 1", [tracker.get_id()])
        row = c.fetchone()
        if row is None:
            return None
        for n in range(len(position.columns)):
            position.values[position.columns[n]] = row[n]
        position.loaded = True
        position.is_new = False
        position.id = position.values["ROWID"]
        return position

    @staticmethod
    def get_last_day_for_tracker(db, tracker: Tracker):
        p = Position(db)
        c = p._lutraDb_db.connection.cursor()
        positions = []
        c.execute(
            f"SELECT {','.join(p.columns)} FROM Positions WHERE TrackerID=? AND Timestamp>? ORDER BY Timestamp",
            [tracker.get_id(), time.time() - (24 * 60 * 60)])
        for row in c.fetchall():
            position = Position(db)
            for n in range(len(position.columns)):
                position.values[position.columns[n]] = row[n]
            position.loaded = True
            position.is_new = False
            position.id = position.values["ROWID"]
            positions.append(position)
        return positions

    @staticmethod
    def get_all_for_tracker(db, tracker: Tracker):
        p = Position(db)
        c = p._lutraDb_db.connection.cursor()
        positions = []
        c.execute(
            f"SELECT {','.join(p.columns)} FROM Positions WHERE TrackerID=? ORDER BY Timestamp",
            [tracker.get_id(), time.time() - (24 * 60 * 60)])
        for row in c.fetchall():
            position = Position(db)
            for n in range(len(position.columns)):
                position.values[position.columns[n]] = row[n]
            position.loaded = True
            position.is_new = False
            position.id = position.values["ROWID"]
            positions.append(position)
        return positions

    @getter
    def get_tracker_id(self):
        return self.values["TrackerID"]

    @setter
    def set_tracker_id(self, tracker_id):
        self.values["TrackerID"] = tracker_id

    @getter
    def get_timestamp(self):
        return self.values["Timestamp"]

    @setter
    def set_timestamp(self, timestamp):
        self.values["Timestamp"] = timestamp

    @getter
    def get_latitude(self):
        return self.values["Latitude"]

    @setter
    def set_latitude(self, latitude):
        self.values["Latitude"] = latitude

    @getter
    def get_longitude(self):
        return self.values["Longitude"]

    @setter
    def set_longitude(self, longitude):
        self.values["Longitude"] = longitude
        