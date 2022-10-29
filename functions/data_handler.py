import os
import sqlite3
import errno
from PyQt5.QtCore import *
import time
from psycopg2 import sql

from functions.analysis import WorkerSignals

db = os.path.join(os.getcwd(), "database", "db.sqlite3")

def scrub(string_item):
    return ''.join((chr for chr in string_item if chr.isalnum() or chr == "_"))

def connect(db_path):
    """Connects to SQLITE3 database

    Args:
        db_path (string): path to database location. Relative to install.

    Raises:
        FileNotFoundError: File is not found at above location

    Returns:
        connection: database connection
        cur: connection cursor
    """
    try:
        if not os.path.exists(db_path):
            raise FileNotFoundError
    except FileNotFoundError as e:
        print(f"Error {errno.ENOENT} - {os.strerror(errno.ENOENT)} - {db_path}")
        print("Empty database will be created in the noted location.")
        pass

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        return [conn, cur]
    except ConnectionError:
        print("Cannot Connect to the database file")


def disconnect(conn, cur):
    """Disconnects an existing database connection

    Args:
        conn (object): database conenction object
        cursor (object): connection cursor object

    Raises:
        FileNotFoundError: _description_
    """

    try:
        cur.close()
        conn.close()
        print("Database succesfully disconnected")

    except ConnectionError:
        print("Cannot Connect to the database file")

def initialize_database():
        try:
            connection, cursor = connect(db)
            database_file_table_check = "SELECT * FROM file_profiles;"
            database_info_table_check = "SELECT * FROM file_profile_info_locations;"
            _ = cursor.execute(database_file_table_check)
            _ = cursor.execute(database_info_table_check)
            print("Database found with proper tables.")
            tables_initialized = True
        except sqlite3.DatabaseError as e:
            print(f"DB Initialization error: {e}")
            print("Initializing database tables...")
            tables_initialized = False
            pass
        finally:
            disconnect(connection, cursor)

        if not tables_initialized:
            try:
                connection, cursor = connect(db)
                database_initialization = """CREATE TABLE IF NOT EXISTS file_profiles (
                    unique_file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_file_itentifier_text TEXT NOT NULL UNIQUE,
                    unique_id_x1 REAL,
                    unique_id_x2 REAL,
                    unique_id_y1 REAL,
                    unique_id_y2 REAL
                    );"""
                cursor.execute(database_initialization)

                _ = cursor.execute(database_file_table_check)
                print("file_profiles table successfully created")

                database_initialization = """CREATE TABLE IF NOT EXISTS file_profile_info_locations (
                    info_unique_id INTEGER PRIMARY KEY,
                    file_unique_id INTEGER,
                    description TEXT,
                    regex TEXT,
                    info_location_x1 REAL,
                    info_location_x2 REAL,
                    info_location_y1 REAL,
                    info_location_y2 REAL,
                    FOREIGN KEY(file_unique_id) REFERENCES file_profiles(unique_file_id)
                    );"""
                cursor.execute(database_initialization)

                _ = cursor.execute(database_info_table_check)
                print("file_profile_info_locations table successfully created")
                print("Database and all tables are successfully initialized.")

            except sqlite3.DatabaseError as e:
                print(f"DB Initialization error: {e}")
            finally:
                disconnect(connection, cursor)


def fetch_table_names():
    connection, cursor = connect(db)
    table_names_sql = "SELECT name FROM sqlite_master WHERE type='table'"
    table_names = cursor.execute(table_names_sql).fetchall()
    table_names = [table_name[0] for table_name in table_names if "sqlite_sequence" not in table_name[0]]
    print(table_names)
    return table_names


class fetch_data(QRunnable):
    

    def __init__(self, database_table):
        super(fetch_data, self).__init__()
        self.database_fetch_results = []
        self.signals = WorkerSignals()
        self.database_table = database_table
    
    @pyqtSlot()
    def run(self):
        connection, cursor = connect(db)

        query = f"SELECT * FROM {scrub(self.database_table)}"
        print(query)
        try:
            self.database_fetch_results = cursor.execute(query).fetchall()
            print(self.database_fetch_results)
            self.signals.result.emit(self.database_fetch_results)
        except sqlite3.DatabaseError as e:
            print(e)
            self.signals.result.emit([])
        finally:
            disconnect(connection, cursor)

    

        



# add_data = """INSERT INTO file_profiles(unique_file_itentifier_text, unique_id_x1, unique_id_x2, unique_id_y1, unique_id_y2) VALUES(?,?,?,?,?)"""
# data = [("test report", 1200, 1700, 0, 150),
# ("lacement", 1200, 1700, 0, 150),
# ("density", 1200, 1700, 0, 150)]

# for data_entry in data:
#     try:
#         cursor.execute(add_data, data_entry)
#         connection.commit()
#     except sqlite3.IntegrityError as e:
#         print(f"Error inserting data: {e}")
#         pass


# add_data = """INSERT INTO file_profile_info_locations(file_unique_id,
#             description,
#             info_location_x1,
#             info_location_x2,
#             info_location_y1,
#             info_location_y2)
#             VALUES(?,?,?,?,?,?);"""

# data = [["lacement", "project number", 380, 660, 310, 340],
#         ["lacement", "date placed", 1280, 1420, 645, 680],
#         ["test report", "project number", 1150, 1475, 315, 350],
#         ["test report", "set number", 250, 350, 630, 670],
#         ["test report", "date cast", 1270, 1450, 630, 670],
#         ["test report", "break strengths", 1200, 1320, 760, 1200],
#         ["test report", "break ages", 400, 475, 760, 1200],
#         ["density", "project number", 1050, 1550, 290, 350],
#         ["density", "date placed", 300, 475, 660, 725]
#         ]


# for i, data_entry in enumerate(data):
#     file_id_select = "SELECT unique_file_id FROM file_profiles WHERE unique_file_itentifier_text = ?;"
#     file_id = cursor.execute(file_id_select, (data_entry[0],))
#     data[i][0] = file_id.fetchone()[0]


# cursor.executemany(add_data, data)
# connection.commit()


