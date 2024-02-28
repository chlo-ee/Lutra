from LutraDB.objects.db_object import DbObject, getter, setter


class LutraMeta(DbObject):
    def __init__(self, db):
        super().__init__(db)
        self._lutraDb_tableName = "LutraMeta"
        self.columns = ["ROWID", "Key", "Value"]

    @getter
    def get_key(self):
        return self.values["Key"]

    @setter
    def set_key(self, key):
        self.values["Key"] = key

    @getter
    def get_value(self):
        return self.values["Value"]

    @setter
    def set_value(self, value):
        self.values["Value"] = value

    @staticmethod
    def load_as_dict(db):
        dictionary = {}

        try:
            cursor = db.connection.cursor()
            cursor.execute(f"SELECT Key, Value FROM LutraMeta")
            for row in cursor.fetchall():
                dictionary[row[0]] = row[1]
        except:
            print("[LutraDB] Meta table not found. Staring over.")
        return dictionary

    @staticmethod
    def get_from_key(db, key):
        meta = LutraMeta(db)
        c = meta._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(meta.columns)} FROM LutraMeta WHERE Key=? LIMIT 1", [key])
        row = c.fetchone()
        if row is None:
            return None
        for n in range(len(meta.columns)):
            meta.values[meta.columns[n]] = row[n]
        meta.loaded = True
        meta.is_new = False
        meta.id = meta.values["ROWID"]
        return meta

    @staticmethod
    def save_from_dict(db, dictionary: dict):
        for key in dictionary.keys():
            meta = LutraMeta.get_from_key(db, key)
            if not meta:
                meta = LutraMeta(db)
                meta.set_key(key)
            meta.set_value(dictionary[key])
            meta.save_record()
