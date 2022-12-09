import os
import sqlite3
import errno
from PyQt5.QtCore import *
import time

db_file_path = os.path.join(os.getcwd(), "database", "db.sqlite3")

class WorkerSignals(QObject):
    """Class of signals to be used from threaded processes"""
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)
    progress = pyqtSignal(int)

def scrub(string_item):
    """Helps prevent SQL injection by only allowing alpha-numeric, "_", "-", ".", and " " characters

    Args:
        string_item (str): string used in sql query

    Returns:
        str: scrubbed string
    """
    try:
        scrubbed = ''.join((chr for chr in string_item if chr.isalnum() or chr in ["_", "-", ".", " "]))
        return  scrubbed
    except TypeError:
        print(f"Scrub Error: Text does not need scrubbing - {string_item}")
        return string_item
    

def db_connect(db_path):
    """Connects to SQLITE3 database

    Args:
        db_path (string): path to database location. Relative to install.

    Raises:
        FileNotFoundError: File is not found at above location

    Returns:
        connection: database connection
        cur: connection cursor
    """

    # Check if database exists at path
    try:
        if not os.path.exists(db_path):
            raise FileNotFoundError
    except FileNotFoundError as e:
        print(f"Error {errno.ENOENT} - {os.strerror(errno.ENOENT)} - {db_path}")
        print("Empty database will be created in the noted location.")
        pass

    # try to connect
    try:
        conn = sqlite3.connect(db_path)

        # Necessary to allow for foriegn keys so upon deletion, children get deleted as well
        conn.execute("PRAGMA foreign_keys = 1")

        cur = conn.cursor()
        return [conn, cur]
    except ConnectionError:
        print("Cannot Connect to the database file")


def db_disconnect(conn, cur):
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
        # print("Database succesfully disconnected")
    except ConnectionError:
        print("Cannot Connect to the database file")

def initialize_database():
    """Checks if the database and tables exists and if not will create the database and intialize the necessary tables."""


    try:
        connection, cursor = db_connect(db_file_path)

        try:
            database_profile_table_check = """SELECT * FROM profiles;"""
            database_paramater_table_check = """SELECT * FROM profile_paramaters;"""
            project_data_check = """SELECT * FROM project_data;"""
            _ = cursor.execute(database_profile_table_check)
            _ = cursor.execute(database_paramater_table_check)
            _ = cursor.execute(project_data_check)
            tables_initialized = True
            print("Database found with proper tables.")
        except sqlite3.DatabaseError as e:
            print(f"DB Initialization error: {e}")
            print("Initializing database tables...")
            tables_initialized = False
            pass
        finally:
            db_disconnect(connection, cursor)
    except ConnectionError as e:
        print(e)

    if not tables_initialized:
        try:
            connection, cursor = db_connect(db_file_path)
            try:
                database_initialization = """CREATE TABLE IF NOT EXISTS profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_identifier_text TEXT NOT NULL,
                    unique_profile_name TEXT NOT NULL UNIQUE,
                    x_1 REAL,
                    x_2 REAL,
                    y_1 REAL,
                    y_2 REAL,
                    file_naming_format TEXT
                    );"""
                cursor.execute(database_initialization)

                _ = cursor.execute(database_profile_table_check)
                print("profiles table successfully created")

                database_initialization = """CREATE TABLE IF NOT EXISTS profile_paramaters (
                    paramater_id INTEGER PRIMARY KEY,
                    profile_id INTEGER,
                    description TEXT,
                    regex TEXT,
                    x_1 REAL,
                    x_2 REAL,
                    y_1 REAL,
                    y_2 REAL,
                    example_text TEXT,
                    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE
                    );"""
                cursor.execute(database_initialization)

                _ = cursor.execute(database_paramater_table_check)
                print("profile_paramaters table successfully created")

                database_initialization = """CREATE TABLE IF NOT EXISTS project_data (
                        id INTEGER PRIMARY KEY,
                        project_number TEXT UNIQUE NOT NULL,
                        directory TEXT NOT NULL,
                        email_to TEXT NOT NULL,
                        email_cc TEXT,
                        email_bcc TEXT,
                        email_subject TEXT NOT NULL
                        );"""
                cursor.execute(database_initialization)

                _ = cursor.execute(project_data_check)
                print("project_data table successfully created")
                    
                print("Database and all tables are successfully initialized.")

            except sqlite3.DatabaseError as e:
                print(f"DB Initialization error: {e}")
                raise
            finally:
                db_disconnect(connection, cursor)
        except ConnectionError as e:
            print(e)
            raise


def fetch_active_params(file_profile_name):
    """Get active paramaters for a file_profile

    Args:
        file_profile_name (str): unique file profile name

    Returns:
        list: Format [(paramater_id, description, example_text)]
    """    
    try:
        connection, cursor = db_connect(db_file_path)
        try:
            file_profile_id_query = """SELECT profile_id FROM profiles WHERE unique_profile_name=?"""
            file_profile_id = cursor.execute(file_profile_id_query, (file_profile_name,)).fetchone()[0]
            active_params_query = """SELECT paramater_id, description, example_text FROM profile_paramaters WHERE profile_id=?"""
            active_params = cursor.execute(active_params_query, (file_profile_id,)).fetchall()
            return [("-1", "doc_num", "01")] + active_params
        except (TypeError, sqlite3.DatabaseError) as e:
            return []
        finally:
            db_disconnect(connection, cursor)
    except ConnectionError as e:
        print(e)

def fetch_file_profiles():
    """Fetces the file_profile data to display to user in dropdowns

    Returns:
        list: Format [[file_profile_name, identifier_text]]
    """    
    try:
        connection, cursor = db_connect(db_file_path)
        try:
            file_profiles_query = """SELECT unique_profile_name, profile_identifier_text FROM profiles"""
            profiles = cursor.execute(file_profiles_query).fetchall()
            if not profiles:
                return [["No Profiles Found",""],]
            return [["Choose File Profile",""]] + profiles
        except sqlite3.DatabaseError as e:
            return [["Database Error",""],]
        finally:
            db_disconnect(connection, cursor)
    except ConnectionError as e:
        print(e)

def update_file_profile_file_name_pattern(file_profile_name, pattern, conn, cur):
    """Updates the file naming scheme in the database for a file_profile

    Args:
        file_profile_name (str): Unique profile name to update
        pattern (str): File naming pattern for analyzed files
        conn (SQLite3 Connection): Open connection to SQLite3 database
        cur (SQLite3 Connection Cursor): Open Cursor to SQLite3 Connection
    """    
    try:
        file_profiles_query = """UPDATE profiles SET file_naming_format=? WHERE profile_identifier_text=?"""
        cur.execute(file_profiles_query, (pattern, file_profile_name,)).fetchall()
        # Conn gets closed after where function is initially called
        conn.commit()
    except sqlite3.DatabaseError as e:
        print(e)


def fetch_table_names():
    """Fetches table names in database for users to choose in dorpdown list

    Returns:
        List: List of table names
    """    
    try:
        connection, cursor = db_connect(db_file_path)
        try:
            table_names_sql = """SELECT name FROM sqlite_master WHERE type='table'"""
            table_names = cursor.execute(table_names_sql).fetchall()
            table_names = [table_name[0] for table_name in table_names if "sqlite_sequence" not in table_name[0]]
            if not table_names:
                return ["No Tables Found",]
            return ["Choose Table"] + table_names
        except sqlite3.DatabaseError as e:
            return ["No Tables Found",]
        finally:
            db_disconnect(connection, cursor)
    except ConnectionError as e:
        print(e)


class fetch_data(QRunnable):
    """Class used to thread the data fetching of database results"""
    def __init__(self, database_table):
        super(fetch_data, self).__init__()
        self.database_fetch_results = []
        self.signals = WorkerSignals()
        self.database_table = database_table
    
    @pyqtSlot()
    def run(self):
        """Fetcehs all database results from a database table"""

        try:
            connection, cursor = db_connect(db_file_path)
            # Probably not proper way to mitigate SQL injections but good enough since table name string is not user supplied
            query = f"""SELECT * FROM {scrub(self.database_table)}"""
            try:
                self.database_fetch_results = cursor.execute(query).fetchall()
                names = list(map(lambda x: x[0], cursor.description))
                self.signals.result.emit([self.database_fetch_results, names])
            except sqlite3.DatabaseError as e:
                print(e)
                self.signals.result.emit([])
            finally:
                db_disconnect(connection, cursor)
        except ConnectionError as e:
            print(e)
