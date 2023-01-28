from PySide6 import QtCore
import contextlib
import os
import sqlite3
import errno
import csv
import typing


class MainModel(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.database_path = os.path.join(os.getcwd(), "database", "db.sqlite3")

    class WorkerSignals(QtCore.QObject):
        """Class of signals to be used from threaded processes"""

        finished = QtCore.Signal()
        error = QtCore.Signal(tuple)
        result = QtCore.Signal(list)
        progress = QtCore.Signal(int)

    @contextlib.contextmanager
    def db_connection(self, db_file_path: str) -> sqlite3.Connection:
        connection = sqlite3.connect(db_file_path)
        try:
            yield connection
        finally:
            connection.close()

    def scrub(self, string_item):
        """Used to clean up OCR results as well as help prevent SQL injection/errors.

        Args:
            string_item (str): string to be cleaned

        Returns:
            str: Initial string with only alpha-numeric, "_", "-", ".", and " " characters remaining
        """
        try:
            scrubbed = "".join(
                (
                    chr
                    for chr in string_item
                    if chr.isalnum() or chr in ["_", "-", ".", " "]
                )
            )
            return scrubbed
        except TypeError:
            print(f"Scrub Error: Text does not need scrubbing - {string_item}")
            return string_item

    def initialize_database(self):
        """Checks if the database and tables exists and if not will create the database and intialize the necessary tables."""
        
        tables_initialized = False
        
        with self.db_connection(self.database_path) as connection:
            database_profile_table_check = """SELECT * FROM profiles;"""
            database_parameter_table_check = """SELECT * FROM profile_parameters;"""
            project_data_check = """SELECT * FROM project_data;"""
            try:
                _ = connection.cursor().execute(database_profile_table_check)
                _ = connection.cursor().execute(database_parameter_table_check)
                _ = connection.cursor().execute(project_data_check)
                tables_initialized = True
                print("Database found with proper tables.")
            except sqlite3.DatabaseError as e:
                print(f"DB Initialization error: {e}")
                print("Initializing database tables...")
                tables_initialized = False

        if not tables_initialized:
            with self.db_connection(self.database_path) as connection:
                try:
                    database_initialization = """CREATE TABLE IF NOT EXISTS profiles (
                        profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        profile_identifier_text TEXT NOT NULL,
                        unique_profile_name TEXT NOT NULL UNIQUE,
                        x_1 REAL,
                        x_2 REAL,
                        y_1 REAL,
                        y_2 REAL,
                        file_naming_format TEXT,
                        count INT DEFAULT 0
                        );"""
                    connection.cursor().execute(database_initialization)

                    _ = connection.cursor().execute(database_profile_table_check)
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
                    connection.cursor().execute(database_initialization)

                    _ = connection.cursor().execute(database_parameter_table_check)
                    print("profile_parameters table successfully created")

                    database_initialization = """CREATE TABLE IF NOT EXISTS project_data (
                            id INTEGER PRIMARY KEY,
                            project_number TEXT UNIQUE NOT NULL,
                            directory TEXT,
                            email_to TEXT,
                            email_cc TEXT,
                            email_bcc TEXT,
                            email_subject TEXT
                            );"""
                    connection.cursor().execute(database_initialization)

                    _ = connection.cursor().execute(project_data_check)
                    print("project_data table successfully created")

                    print("Database and all tables are successfully initialized.")

                except sqlite3.DatabaseError as e:
                    print(f"DB Initialization error: {e}")
                    raise

    def fetch_active_parameters(
        self, file_profile_name: str
    ) -> tuple[list[tuple[str]], str]:
        """Get active parameters for a file_profile

        Args:
            file_profile_name (str): unique file profile name

        Returns:
            tuple: Format ([(parameter_id, description, example_text)], file_naming_scheme)
        """
        with self.db_connection(self.database_path) as connection:
            try:
                file_profile_id_query = """SELECT profile_id, file_naming_format FROM profiles WHERE unique_profile_name=?"""
                file_profile_data = connection.cursor().execute(
                    file_profile_id_query, (file_profile_name,)
                ).fetchone()
                file_profile_id, file_naming_scheme = (
                    file_profile_data[0],
                    file_profile_data[1],
                )
                active_params_query = """SELECT parameter_id, description, example_text FROM profile_parameters WHERE profile_id=?"""
                active_params = connection.cursor().execute(
                    active_params_query, (file_profile_id,)
                ).fetchall()
                return [("-1", "doc_num", "01")] + active_params, file_naming_scheme
            except (TypeError, sqlite3.DatabaseError) as e:
                return [], []


    def fetch_file_profiles(self) -> list[str]:
        """Fetces the file_profile data to display to user in dropdowns

        Returns:
            list: Format [[file_profile_name, identifier_text]]
        """
        with self.db_connection(self.database_path) as connection:
            try:
                file_profiles_query = """SELECT unique_profile_name, profile_identifier_text FROM profiles"""
                profiles = connection.cursor().execute(file_profiles_query).fetchall()
                if not profiles:
                    return []
                return profiles
            except sqlite3.DatabaseError as e:
                return []

    def fetch_profile_file_name_pattern(self, profile_name: str) -> str:
        with self.db_connection(self.database_path) as connection:
            try:
                profile_file_name_scheme_query = """SELECT file_naming_format FROM profiles WHERE unique_profile_name = ?"""
                current_profile_name = connection.cursor().execute(
                    profile_file_name_scheme_query, (self.scrub(profile_name),)
                ).fetchone()
                if not current_profile_name:
                    return []
                return current_profile_name[0]
            except sqlite3.DatabaseError as e:
                return []

    def update_file_profile_file_name_pattern(self, profile_name, pattern):
        """Updates the file naming scheme in the database for a file_profile

        Args:
            file_profile_name (str): Unique profile name to update
            pattern (str): File naming pattern for analyzed files
        """
        with self.db_connection(self.database_path) as connection:
            try:
                file_profiles_query = """UPDATE profiles SET file_naming_format=? WHERE unique_profile_name=?"""
                connection.cursor().execute(
                    file_profiles_query,
                    (
                        pattern,
                        profile_name,
                    ),
                )
                connection.commit()
            except sqlite3.DatabaseError as e:
                print(e)

    def fetch_table_names(self):
        """Fetches table names in database for users to choose in dropdown list

        Returns:
            List: List of table names
        """
        with self.db_connection(self.database_path) as connection:
            try:
                table_names_sql = (
                    """SELECT name FROM sqlite_master WHERE type='table'"""
                )
                table_names = connection.cursor().execute(table_names_sql).fetchall()
                table_names = [
                    table_name[0]
                    for table_name in table_names
                    if "sqlite_sequence" not in table_name[0]
                ]
                if not table_names:
                    return [
                        "No Tables Found",
                    ]
                return ["Choose Table"] + table_names
            except sqlite3.DatabaseError as e:
                return [
                    "No Tables Found",
                ]

    def fetch_data(self, database_table: str) -> list[list[str],list[str]]:

        """Fetcehs all database results from a database table"""
        results = None
        with self.db_connection(self.database_path) as connection:
            # Probably not proper way to mitigate SQL injections but good enough since database_table string is not user supplied
            query = f"""SELECT project_number, directory, email_to, email_cc, email_bcc, email_subject FROM {self.scrub(database_table)}"""
            try:
                database_fetch_results = connection.cursor().execute(query).fetchall()
                names = list(map(lambda x: x[0], connection.cursor().description))
                results = [database_fetch_results, names]
            except sqlite3.DatabaseError as e:
                print(e)

        return results

    def delete_project_data_entry(self, project_number: str) -> str:

        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                delete_statement = (
                    """DELETE FROM project_data WHERE project_number=?;"""
                )
                connection.cursor().execute(delete_statement, (project_number,))
                connection.commit()
            except Exception as e:
                msg = f"Error updating Project Data: {e}"

        return msg

    def update_project_data(self, old_data, new_data):
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                update_statement = """UPDATE project_data SET project_number=?, directory=?, email_to=?, email_cc=?, email_bcc=?, email_subject=? WHERE project_number=?;"""
                data = [
                    new_data[key]
                    for key in [
                        "project_number",
                        "directory",
                        "email_to",
                        "email_cc",
                        "email_bcc",
                        "email_subject",
                    ]
                ]
                data.append(old_data["project_number"])
                connection.cursor().execute(update_statement, data)
                connection.commit()
            except Exception as e:
                msg = f"Error updating Project Data: {e}"

        return msg

    def add_new_project_data(self, new_data):
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                new_data_query = """INSERT INTO project_data (project_number,directory,email_to,email_cc,email_bcc,email_subject) VALUES(?,?,?,?,?,?);"""
                data = [
                    new_data[key]
                    for key in [
                        "project_number",
                        "directory",
                        "email_to",
                        "email_cc",
                        "email_bcc",
                        "email_subject",
                    ]
                ]
                connection.cursor().execute(new_data_query, data)
                connection.commit()
            except Exception as e:
                msg = f"{e}"

        return msg
    
    def export_project_data_thread(self, export_location):
        ExportProjectDataThread()


class ImportProjectDataThread(QtCore.QRunnable):
    def __init__(
            self, project_data: list[str], 
            worker_signals: MainModel.WorkerSignals,
            db_connection: typing.Callable,
            database_path: str
        ):
        super(ImportProjectDataThread, self).__init__()
        self.worker_signals: worker_signals
        self.db_connection: db_connection
        self.database_path: database_path
        self.import_project_data = project_data

    @QtCore.Slot()
    def run(self):
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                progress = 33
                results = connection.cursor().execute(
                    """SELECT project_number FROM project_data;"""
                ).fetchall()
                result_list = []
                for i, result in enumerate(results):
                    result_list.append(result[0])
                    self.signals.progress.emit(int((1 + i) / len(results) * progress))

                # Remove non-unique project numbers before importing
                # Removing them now and using executemany was WAY faster than not removing duplicates and using execute to insert rows individually
                # and letting unique constraint just go to exception
                temp_project_data = []
                for i, project in enumerate(self.import_project_data):
                    self.signals.progress.emit(
                        progress
                        + int((1 + i) / len(self.import_project_data) * progress)
                    )
                    if project[0] not in result_list:
                        temp_project_data.append(project)
                self.import_project_data = temp_project_data

                msg = connection.cursor().executemany(
                    """INSERT INTO project_data (project_number,directory,email_to,email_cc,email_bcc,email_subject) VALUES(?,?,?,?,?,?);""",
                    self.import_project_data,
                )
                connection.commit()
                self.signals.progress.emit(99)
            except Exception as e:
                msg = f"Error: {e}"
            finally:
                self.signals.result.emit([msg])


class ExportProjectDataThread(QtCore.QRunnable):
    def __init__(
        self,
        export_location,
        worker_signals: MainModel.WorkerSignals,
        db_connection: typing.Callable,
        database_path: str,
    ):
        super(ExportProjectDataThread, self).__init__()
        self.signals = worker_signals()
        self.export_location = export_location
        self.db_connection = db_connection
        self.database_path = database_path

    @QtCore.Slot()
    def run(self):
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:

                results = connection.cursor().execute("""SELECT * FROM project_data;""").fetchall()

                # revove id col
                results = [result[1:] for result in results]
                headers = [i[0] for i in connection.cursor().description]
                headers = headers[1:]

                self.signals.progress.emit(25)
                with open(
                    os.path.abspath(os.path.join(self.export_location, "exported.csv")),
                    "w",
                    newline="",
                ) as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(headers)  # write headers
                    self.signals.progress.emit(50)
                    csv_writer.writerows(results)
                    self.signals.progress.emit(100)
            except Exception as e:
                msg = f"Error: {e}"
            finally:
                self.signals.result.emit([msg])


class DeleteProjectDataThread(QtCore.QRunnable):
    def __init__(
        self,
        worker_signals: MainModel.WorkerSignals,
        db_connection: typing.Callable,
        database_path: str,
    ):
        super(DeleteProjectDataThread, self).__init__()
        self.signals = worker_signals()
        self.db_connection = db_connection
        self.database_path = database_path

    @QtCore.Slot()
    def run(self):
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                self.signals.progress.emit(50)
                connection.cursor().execute("""DELETE FROM project_data;""")
                connection.commit()
                self.signals.progress.emit(100)
            except Exception as e:
                msg = f"Error: {e}"
            finally:
                self.signals.result.emit([msg])
