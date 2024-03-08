import sqlite3
import os

from LutraDB.migrations import migrations
from LutraDB.objects.lutra_meta import LutraMeta


class LutraDB:
    def __init__(self, file):
        self.db_version = 6
        run_db_init = not os.path.isfile(file)
        self.connection = sqlite3.connect(file)
        self.metadata = {}
        if run_db_init:
            self.init_database()

    def check_upgrades(self):
        self.metadata = LutraMeta.load_as_dict(self)
        print(self.metadata)
        current_version = 0
        if "DB_VERSION" in self.metadata:
            current_version = self.metadata["DB_VERSION"]

        if current_version < self.db_version:
            print("[LutraDB] Upgrading database...")
            cursor = self.connection.cursor()
            for i in range(current_version, self.db_version):
                print(f"[LutraDB] Running migration scripts from DB version {i} to {i+1}")
                for migration in migrations[i]:
                    print(f"[LutraDB]      {migration}")
                    cursor.executescript(migration)
            self.connection.commit()
            self.metadata["DB_VERSION"] = self.db_version
            LutraMeta.save_from_dict(self, self.metadata)

            print("[LutraDB] Migration done.")

    def init_database(self):
        with open('db_init.sql', 'r') as init_script_f:
            init_script = init_script_f.read()
            cursor = self.connection.cursor()
            cursor.executescript(init_script)

        self.connection.commit()
        db_version_meta = LutraMeta(self)
        db_version_meta.set_key("DB_VERSION")
        db_version_meta.set_value(self.db_version)
        db_version_meta.save_record()
