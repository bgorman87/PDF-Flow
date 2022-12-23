import os
import sqlite3
import errno
from PySide6.QtCore import *
import time
import csv

import debugpy

db_file_path = os.path.join(os.getcwd(), "database", "db.sqlite3")

class WorkerSignals(QObject):
    """Class of signals to be used from threaded processes"""
    finished = Signal()
    error = Signal(tuple)
    result = Signal(list)
    progress = Signal(int)

def scrub(string_item):
    """Used to clean up OCR results as well as help prevent SQL injection/errors.

    Args:
        string_item (str): string to be cleaned

    Returns:
        str: Initial string with only alpha-numeric, "_", "-", ".", and " " characters remaining
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
            database_parameter_table_check = """SELECT * FROM profile_parameters;"""
            project_data_check = """SELECT * FROM project_data;"""
            _ = cursor.execute(database_profile_table_check)
            _ = cursor.execute(database_parameter_table_check)
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

                database_initialization = """CREATE TABLE IF NOT EXISTS profile_parameters (
                    parameter_id INTEGER PRIMARY KEY,
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

                _ = cursor.execute(database_parameter_table_check)
                print("profile_parameters table successfully created")

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
    """Get active parameters for a file_profile

    Args:
        file_profile_name (str): unique file profile name

    Returns:
        list: Format [(parameter_id, description, example_text)]
    """    
    try:
        connection, cursor = db_connect(db_file_path)
        try:
            file_profile_id_query = """SELECT profile_id, file_naming_format FROM profiles WHERE unique_profile_name=?"""
            file_profile_data = cursor.execute(file_profile_id_query, (file_profile_name,)).fetchone()
            file_profile_id, file_naming_scheme = file_profile_data[0], file_profile_data[1]
            active_params_query = """SELECT parameter_id, description, example_text FROM profile_parameters WHERE profile_id=?"""
            active_params = cursor.execute(active_params_query, (file_profile_id,)).fetchall()
            return [("-1", "doc_num", "01")] + active_params, file_naming_scheme
        except (TypeError, sqlite3.DatabaseError) as e:
            return [], []
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
        file_profiles_query = """UPDATE profiles SET file_naming_format=? WHERE unique_profile_name=?"""
        cur.execute(file_profiles_query, (pattern, file_profile_name,))
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


def fetch_data(database_table):

    """Fetcehs all database results from a database table"""
    results = None
    try:
        connection, cursor = db_connect(db_file_path)
        # Probably not proper way to mitigate SQL injections but good enough since database_table string is not user supplied
        query = f"""SELECT project_number, directory, email_to, email_cc, email_bcc, email_subject FROM {scrub(database_table)}"""
        try:
            database_fetch_results = cursor.execute(query).fetchall()
            names = list(map(lambda x: x[0], cursor.description))
            results = [database_fetch_results, names]
        except sqlite3.DatabaseError as e:
            print(e)
        finally:
            db_disconnect(connection, cursor)
    except ConnectionError as e:
        print(e)
    
    return results

class ImportProjectDataThread(QRunnable):
    def __init__(self, project_data):
        super(ImportProjectDataThread, self).__init__()
        self.signals = WorkerSignals()
        self.import_project_data = project_data

    @Slot()
    def run(self):
        # debugpy.debug_this_thread()
        try:
            connection, cursor = db_connect(db_file_path)
            msg = None
            try:
                progress = 33       
                results = cursor.execute("""SELECT project_number FROM project_data;""").fetchall()
                result_list = []
                for i, result in enumerate(results):
                    result_list.append(result[0])
                    self.signals.progress.emit(int((1+i)/len(results)*progress))
                
                
                # Remove non-unique project numbers before importing
                # Removing them now and using executemany was WAY faster than not removing duplicates and using execute to insert rows individually 
                # and letting unique constraint just go to exception
                temp_project_data = []
                for i, project in enumerate(self.import_project_data):
                    self.signals.progress.emit(progress + int((1+i)/len(self.import_project_data)*progress))
                    if project[0] not in result_list:
                        temp_project_data.append(project)
                self.import_project_data = temp_project_data     
                
                cursor.executemany("""INSERT INTO project_data (project_number,directory,email_to,email_cc,email_bcc,email_subject) VALUES(?,?,?,?,?,?);""", self.import_project_data)
                connection.commit()
                self.signals.progress.emit(99)
            except Exception as e:
                msg = f'Error: {e}'
            finally:
                db_disconnect(connection, cursor)
                self.signals.result.emit([msg])
        except ConnectionError as e:
            msg = f'Error: {e}'
            self.signals.result.emit([msg])


class ExportProjectDataThread(QRunnable):
    def __init__(self, export_location):
        super(ExportProjectDataThread, self).__init__()
        self.signals = WorkerSignals()
        self.export_location = export_location

    @Slot()
    def run(self):
        # debugpy.debug_this_thread()
        try:
            msg = None
            connection, cursor = db_connect(db_file_path)
            try:

                results = cursor.execute("""SELECT * FROM project_data;""").fetchall()
                
                # revove id col
                results = [result[1:] for result in results]
                headers = [i[0] for i in cursor.description]
                headers = headers[1:]

                self.signals.progress.emit(25)
                with open(os.path.abspath(os.path.join(self.export_location,"exported.csv")), "w", newline="") as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(headers) # write headers
                    self.signals.progress.emit(50)
                    csv_writer.writerows(results)
                    self.signals.progress.emit(100)
            except Exception as e:
                msg = f'Error: {e}'
            finally:
                db_disconnect(connection, cursor)
                self.signals.result.emit([msg])
        except ConnectionError as e:
            msg = f'Error: {e}'
            self.signals.result.emit([msg])

def update_project_data(old_data, new_data):
    try:
        msg = None
        connection, cursor = db_connect(db_file_path)
        try:
            update_statement = """UPDATE project_data SET project_number=?, directory=?, email_to=?, email_cc=?, email_bcc=?, email_subject=? WHERE project_number=?;"""
            data = [new_data[key] for key in ["project_number", "directory", "email_to", "email_cc", "email_bcc", "email_subject"]]
            data.append(old_data["project_number"])
            cursor.execute(update_statement, data)
            connection.commit()
        except Exception as e:
            msg = f"Error updating Project Data: {e}"
        finally:
            db_disconnect(connection, cursor)
    except ConnectionError as e:
            msg = f'Error: {e}'

    return msg