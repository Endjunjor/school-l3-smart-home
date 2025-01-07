import sqlite3
import os.path
import time as t

from exceptions import DBExistsException, DeviceTypeNotFoundException, DeviceNotFoundException

class DBWrapper:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None
        self.cur = None

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def create_db(self):
        self.connection = sqlite3.connect(self.db_name,check_same_thread=False)
        self.connection.row_factory = self.dict_factory
        self.cur = self.connection.cursor()
        return self.cur

    def init_tables(self):
        start = t.time()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT NOT NULL,
                code TEXT NOT NULL,
                message TEXT NOT NULL,
                deviceID INTEGER,
                FOREIGN KEY(deviceID) REFERENCES device(id)
            );
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS device_type (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_type TEXT NOT NULL
            );
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS device (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                devicename TEXT NOT NULL,
                pin INTEGER NOT NULL UNIQUE,
                device_type_id INTEGER NOT NULL,
                roomID INTEGER,
                state INTEGER,
                FOREIGN KEY(device_type_id) REFERENCES device_type(id)
            );
        """)

        # Insert default device types if they don't exist
        self.cur.executemany("""
            INSERT OR IGNORE INTO device_type (id, device_type) VALUES (?, ?);
        """, [(1, 'output'), (2, 'input'), (3, 'virtual_input')])
        time_to_build = t.time() - start
        self.cur.execute("""
            INSERT INTO logs (type, code, message, deviceID)
            VALUES (?, ?, ?, NULL);
        """, ('info', 'startup', f'System initialized in {time_to_build:.2f} secs'))
        self.connection.commit()

    def init_db(self):
        self.create_db()
        return self.cur

    def write_log(self, msg_type: str, code: str, message: str, device_id=None):
        self.cur.execute("""
            INSERT INTO logs (type, code, message, deviceID)
            VALUES (?, ?, ?, ?);
        """, (msg_type, code, message, device_id))
        self.connection.commit()

    def add_device(self, device_name: str, pin: int, device_type: int, room_id = 0):
        device_type = self.cur.execute("""
            SELECT id FROM device_type WHERE device_type = ?;
        """, (device_type,)).fetchone()
        if not device_type:
            raise DeviceTypeNotFoundException(f"Device type {device_type['device_type']} not found")
        try:
            self.cur.execute("""
                INSERT INTO device (devicename, pin, device_type_id, roomID)
                VALUES (?, ?, ?, ?);
            """, (device_name, pin, device_type["id"], room_id))
        except sqlite3.IntegrityError:
            return False
        self.write_log("info", "device_added", f"Successfully added device {device_name} of type {device_type} on pin {pin}")
        self.connection.commit()
        return True

    def remove_device(self, pin):
        pin_is_in_use = self.cur.execute("""
            SELECT pin FROM device WHERE pin = ?;
        """, (pin,)).fetchone()
        if pin_is_in_use:
            self.cur.execute("""
                DELETE FROM device WHERE pin = ?;
            """, (pin,))
            self.write_log("info", "device_removed", f"Successfully removed device on pin {pin}")
            self.connection.commit()
        else:
            raise DeviceNotFoundException(f"Device with pin {pin} not found")

    def get_device(self, pin):
        device = self.cur.execute("""
        SELECT * FROM device WHERE pin = ?;
        """, (pin,)).fetchone()
        
        return device
    
    def get_all_devices(self):
        all_devices = self.cur.execute("""
        SELECT * FROM device ORDER BY roomID DESC;
        """).fetchall()
        return all_devices
    
    def get_all_devices_for_room(self,room_id: int):
        all_devices_for_room = self.cur.execute("""
        SELECT * FROM device WHERE roomID = ?;
        """, (room_id,)).fetchall()

        return all_devices_for_room

    def update_device_state_by_pin(self, pin: int, state: int):
        update = self.cur.execute("""
        UPDATE device SET state = ? WHERE pin = ?;
        """, (state,pin, ))
        self.write_log("INFO", 200 , f"Updated state on pin {pin} to {state}" )
        self.connection.commit()


    def close(self):
        if self.connection:
            self.connection.close()

