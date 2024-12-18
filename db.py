import sqlite3
import os.path
import time as t

from exceptions import DBExistsException, DeviceTypeNotFoundException, DeviceNotFoundException

class DBWrapper:
    def __init__(self, db_name):
        self.db_name = db_name
    
    def create_db(self):
        return sqlite3.connect(self.db_name)
    
    def init_tables(self):
        start = t.time()
        self.cur.execute("CREATE TABLE logs (id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,type TEXT NOT NULL,code TEXT NOT NULL,message TEXT NOT NULL, deviceID INTEGER,FOREIGN KEY(deviceID) REFERENCES device(id));)")
        self.cur.execute("CREATE TABLE device_type (id INTEGER PRIMARY KEY AUTOINCREMENT, device_type TEXT NOT NULL);")
        self.cur.execute("CREATE TABLE device (id INTEGER PRIMARY KEY AUTOINCREMENT, devicename TEXT NOT NULL, pin INTEGER NOT NULL UNIQUE, device_type_id INTEGER NOT NULL, FOREIGN KEY(device_type_id) REFERENCES device_type(id));")
        self.cur.execute("INSERT INTO device_type (id, device_type) VALUES (1, 'output');")
        self.cur.execute("INSERT INTO device_type (id, device_type) VALUES (2, 'input');")
        self.cur.execute("INSERT INTO device_type (id, device_type) VALUES (3, 'virtual_input');")
        time_to_build = t.time() - start
        self.cur.execute(f"INSERT INTO logs (type, code, message, deviceID) VALUES ('info', 'startup', 'System initialized in {time_to_build} secs', NULL);")

    def init_db(self):
        self.cur = self.create_db()
        return self.cur

    def write_log(self, msg_type: str, code: str, message: str, device_id=None):
        if device_id:
            self.cur.execute(f"INSERT INTO logs (type, code, message, deviceID) VALUES ('{msg_type}', '{code}', '{message}','{device_id}');")
        else:
            self.cur.execute(f"INSERT INTO logs (type, code, message, deviceID) VALUES ('{msg_type}', '{code}', '{message}', NULL);")

    def add_device(self, device_name: str, pin: int, device_type: int ):
        device_type_exists = self.cur.execute(f"SELECT id FROM device_type WHERE id = {device_type}").fetchone() is None
        if device_type_exists:
            raise DeviceTypeNotFoundException
        self.cur.execute(f"INSERT INTO device (devicename, pin, device_type_id) VALUES({device_name},{pin},{device_type})")
        self.write_log("info", "device_added", f"Successfully added device {device_name} of type {device_type} on pin {pin} ")
        return True
    
    def remove_device(self, pin):
        pin_is_in_use = self.cur.execute(f"SELECT pin FROM device WHERE pin={pin}").fetchone() is None
        if not pin_is_in_use:
            self.cur.execute(f"DELETE FROM device WHERE pin={pin}")
            self.write_log("info", "device_added", f"Successfully removed device on pin {pin} ")
        else:
            raise DeviceNotFoundException
        

db = DBWrapper("test.db")
db.init_db()
db.add_device("test", 12, 1)
