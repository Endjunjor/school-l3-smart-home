import sqlite3
from collections import defaultdict
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

    def group_by_minute(self, data):
        history_by_minute = defaultdict(list)
        for row in data:
            minute = row["minute_group"]
            history_by_minute[minute].append(row)
        return dict(history_by_minute)

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
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                deviceID INTEGER,
                state INTEGER,
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
    
    def get_all_devices_grouped_by_room(self):
        all_devices = self.cur.execute("""
        SELECT * FROM device ORDER BY roomID DESC;
        """).fetchall()

        grouped_devices = {}

        for device in all_devices:
            roomID = device["roomID"]
            if roomID not in grouped_devices:
                grouped_devices[roomID] = []
            grouped_devices[roomID].append(device)
        
        return grouped_devices


    def update_device_state_by_pin(self, pin: int, state: int):
        update = self.cur.execute("""
        UPDATE device SET state = ? WHERE pin = ?;
        """, (state,pin, ))
        self.write_log("INFO", 200 , f"Updated state on pin {pin} to {state}" )
        self.connection.commit()

    def get_number_of_rooms(self):
        result = self.cur.execute("""
        SELECT DISTINCT roomID FROM device;
        """).fetchall()
        return result
    
    def create_record(self, deviceID, state):
        self.cur.execute("""
            INSERT INTO history (deviceID, state) VALUES (?, ?)
        """, (deviceID, state, ))

        self.connection.commit()
        return True
    
    def get_num_state_updates(self):
        num_updates = self.cur.execute("""
            SELECT COUNT(deviceID) FROM history;
        """)
        return num_updates
    def get_history(self):
        history_entries = self.cur.execute("""
            SELECT 
                strftime('%Y-%m-%d %H:%M', history.timestamp) AS minute_group,
                device.devicename,
                device.id AS device_id,
                device.roomID,
                history.state
            FROM 
                history
            JOIN 
                device ON history.deviceID = device.id
            GROUP BY 
                minute_group, device.id
            ORDER BY 
                minute_group DESC;
        """)
        grouped_data = self.group_by_minute(history_entries)
        return grouped_data

    def close(self):
        if self.connection:
            self.connection.close()

