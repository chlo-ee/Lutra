from LutraDB.objects.tracker import Tracker
from LutraDB.objects.user import User
from LutraDB.objects.db_object import DbObject, getter, setter


class UserTracker(DbObject):
    def __init__(self, db):
        super().__init__(db)
        self._lutraDb_tableName = "UserTrackers"
        self.columns = ["ROWID", "UserID", "TrackerID"]

    @staticmethod
    def get_user_trackers_by_user(db, user: User):
        ut = UserTracker(db)
        c = ut._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(ut.columns)} FROM UserTrackers WHERE UserID=?", [user.get_id()])
        user_trackers = []
        for row in c.fetchall():
            if row is None:
                return None
            user_tracker = UserTracker(db)
            for n in range(len(user_tracker.columns)):
                user_tracker.values[user_tracker.columns[n]] = row[n]
            user_trackers.append(user_tracker)
        return user_trackers


    @staticmethod
    def get_trackers_by_user(db, user: User):
        t = Tracker(db)
        c = t._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(t.columns)} FROM Trackers WHERE ROWID IN (SELECT TrackerID FROM UserTrackers WHERE UserID=?)", [user.get_id()])
        trackers = []
        for row in c.fetchall():
            if row is None:
                return None
            tracker = Tracker(db)
            for n in range(len(tracker.columns)):
                tracker.values[tracker.columns[n]] = row[n]
            trackers.append(tracker)
        return trackers

    @staticmethod
    def check_authorization(db, user: User, tracker: Tracker):
        ut = UserTracker(db)
        c = ut._lutraDb_db.connection.cursor()
        c.execute(f"SELECT ROWID FROM UserTrackers WHERE TrackerID=? AND UserID=? LIMIT 1", [tracker.get_id(), user.get_id()])
        return c.fetchone() is not None

    @getter
    def get_user(self):
        user = User(self._lutraDb_db)
        user.set_id(self.values["UserID"])
        user.load_record()
        return user

    @getter
    def get_tracker(self):
        tracker = Tracker(self._lutraDb_db)
        tracker.set_id(self.values["TrackerID"])
        tracker.load_record()
        return tracker

    @setter
    def set_tracker(self, tracker):
        self.values["TrackerID"] = tracker.get_id()

    @setter
    def set_user(self, user):
        self.values["UserID"] = user.get_id()
