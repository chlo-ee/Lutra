import bcrypt

from LutraDB.objects.db_object import DbObject, getter, setter


class User(DbObject):
    def __init__(self, db):
        super().__init__(db)
        self._lutraDb_tableName = "Users"
        self.columns = ["ROWID", "Name", "Password"]

    @staticmethod
    def get_by_username(db, username):
        user = User(db)
        c = user._lutraDb_db.connection.cursor()
        c.execute(f"SELECT {','.join(user.columns)} FROM Users WHERE Name=? LIMIT 1", [username])
        row = c.fetchone()
        if row is None:
            return None
        for n in range(len(user.columns)):
            user.values[user.columns[n]] = row[n]
        return user

    @getter
    def get_name(self):
        return self.values["Name"]

    @setter
    def set_name(self, name):
        self.values["Name"] = name

    @getter
    def get_password(self):
        return self.values["Password"]

    @setter
    def set_password(self, password):
        self.values["Password"] = password

    def hash_and_set_password(self, password):
        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        self.set_password(hash)

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.get_password())