import sqlite3
import os

class LutraDB:
    def __init__(self, file):
        run_db_init = not os.path.isfile(file)
        self.connection = sqlite3.connect(file)
        if run_db_init:
            self.init_database()

    def init_database(self):
        with open('db_init.sql', 'r') as init_script_f:
            init_script = init_script_f.read()
            cursor = self.connection.cursor()
            cursor.executescript(init_script)
        self.connection.commit()
