import json

from LutraDB.database import LutraDB


def setter(func):
    def _setter(self, *args, **kwargs):
        self.flushed = False
        return func(self, *args, **kwargs)
    return _setter


def getter(func):
    def _getter(self, *args, **kwargs):
        if not self.loaded and self.flushed and self.id is not None:
            self.load_record()
        return func(self, *args, **kwargs)
    return _getter


class DbObject:
    def __init__(self, db: LutraDB):
        self._lutraDb_db = db
        self._lutraDb_tableName: None | str = None
        self.id: None | int = None
        self.columns = []
        self.loaded = False
        self.flushed = True
        self.is_new = True
        self.values = {}

    @setter
    def set_id(self, id: int):
        self.id = id
        self.loaded = False

    @getter
    def get_id(self):
        return self.values["ROWID"]

    def load_record(self):
        c = self._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(self.columns)} FROM {self._lutraDb_tableName} WHERE ROWID=? LIMIT 1", [self.id])
        row = c.fetchone()
        if row is None:
            return
        for n in range(len(self.columns)):
            self.is_new = False
            self.loaded = True
            self.flushed = True
            self.values[self.columns[n]] = row[n]
            if self.columns[n] == "ROWID":
                self.id = row[n]

    def save_record(self):
        c = self._lutraDb_db.connection.cursor()
        if self.is_new:
            statement = f"INSERT INTO {self._lutraDb_tableName} ({','.join(self.values.keys())}) VALUES ({','.join(['?'] * len(self.values))})"
            c.execute(statement, list(self.values.values()))
            self.id = c.lastrowid

        else:
            for key in self.columns:
                if key in self.values.keys():
                    c.execute(f"UPDATE {self._lutraDb_tableName} SET {key}=? WHERE ROWID=?", [self.values[key], self.id])
        c.connection.commit()

    def delete_record(self):
        if not self.is_new:
            c = self._lutraDb_db.connection.cursor()
            c.execute(f"DELETE FROM {self._lutraDb_tableName} WHERE ROWID=?", [self.id])
            c.connection.commit()
