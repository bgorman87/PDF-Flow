import contextlib
import csv
import os
import sqlite3
import typing

# import debugpy
from PySide6 import QtCore
from widgets import loading_widget

from utils.path_utils import resource_path


class MainModel(QtCore.QObject):
    import_progress = QtCore.Signal(int)
    import_result = QtCore.Signal(str)
    export_progress = QtCore.Signal(int)
    export_result = QtCore.Signal(str)
    delete_progress = QtCore.Signal(int)
    delete_result = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.database_path = resource_path("database/db.sqlite3")
        self.database_folder = resource_path(
            "database"
        )
        self.import_data = None
        self._thread_pool = QtCore.QThreadPool()

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

    def scrub(self, string_item: str) -> str:
        """Used to clean up OCR results as well as help prevent SQL injection/errors.

        Args:
            string_item (str): string to be cleaned

        Returns:
            str: Initial string with only alpha-numeric, "_", "-", and "." characters remaining
        """
        try:
            string_item = string_item.strip()
            string_item = string_item.replace("\n", "").replace(" ", "_")

            # Because spaces are replaced with hyphens or underscores, to make it more visually appealing
            # we will remove any duplicate hyphens or underscores. Requires 3 loops total to do.
            for i in range(3, 0, -1):
                string_item = string_item.replace("_"*i, "_")
                string_item = string_item.replace("-"*i, "-")


            scrubbed = "".join(
                (
                    chr
                    for chr in string_item
                    if chr.isalnum() or chr in ["_", "-", "."]
                )
            )
            return scrubbed
        except TypeError:
            return string_item

    def initialize_database(self):
        """Checks if the database and tables exists and if not will create the database and initialize the necessary tables."""

        if not os.path.exists(self.database_folder):
            os.makedirs(self.database_folder)

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
                        email_profile_name TEXT DEFAULT '',
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
                        advanced TEXT DEFAULT '',
                        FOREIGN KEY(profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE
                        );"""
                    connection.cursor().execute(database_initialization)

                    _ = connection.cursor().execute(database_parameter_table_check)
                    print("profile_parameters table successfully created")

                    database_initialization = """CREATE TABLE IF NOT EXISTS secondary_profile_parameters (
                        secondary_parameter_id INTEGER PRIMARY KEY,
                        parameter_id INTEGER,
                        description TEXT,
                        x_1 REAL,
                        x_2 REAL,
                        y_1 REAL,
                        y_2 REAL,
                        advanced TEXT DEFAULT '',
                        comparison_type TEXT DEFAULT '',
                        FOREIGN KEY(parameter_id) REFERENCES profile_parameters(parameter_id) ON DELETE CASCADE
                        );"""
                    connection.cursor().execute(database_initialization)

                    _ = connection.cursor().execute(database_parameter_table_check)
                    print("secondary_profile_parameters table successfully created")

                    database_initialization = """CREATE TABLE IF NOT EXISTS project_data (
                            id INTEGER PRIMARY KEY,
                            project_number TEXT UNIQUE NOT NULL,
                            directory TEXT,
                            description TEXT,
                            email_to TEXT,
                            email_cc TEXT,
                            email_bcc TEXT,
                            email_subject TEXT,
                            email_profile_name TEXT DEFAULT ''
                            );"""
                    connection.cursor().execute(database_initialization)

                    _ = connection.cursor().execute(project_data_check)
                    print("project_data table successfully created")

                    print("Database and all tables are successfully initialized.")

                except sqlite3.DatabaseError as e:
                    print(f"DB Initialization error: {e}")
                    raise

    def fetch_all_profile_template_info(self) -> list[str]:
        with self.db_connection(self.database_path) as connection:
            unique_texts_query = """SELECT profile_id, profile_identifier_text, unique_profile_name FROM profiles"""
            unique_texts = connection.cursor().execute(unique_texts_query).fetchall()

        return unique_texts

    def fetch_profile_rectangle_bounds_by_profile_id(
        self, profile_id: int
    ) -> list[str]:
        with self.db_connection(self.database_path) as connection:
            prof_txt_loc_query = (
                """SELECT x_1, x_2, y_1, y_2 FROM profiles WHERE profile_id=?"""
            )
            [db_x_1, db_x_2, db_y_1, db_y_2] = (
                connection.cursor()
                .execute(prof_txt_loc_query, (profile_id,))
                .fetchone()
            )
        return [db_x_1, db_x_2, db_y_1, db_y_2]

    def delete_profile_by_name(self, profile_name: str):
        with self.db_connection(self.database_path) as connection:
            connection.cursor().execute(
                """DELETE FROM profiles WHERE profile_name=?""",
                (profile_name,),
            )
            connection.commit()

    def delete_profile_by_id(self, profile_id: int):
        with self.db_connection(self.database_path) as connection:
            connection.cursor().execute(
                """DELETE FROM profiles WHERE profile_id=?""",
                (profile_id,),
            )
            connection.commit()

    def rename_template_profile(self, profile_id: int, new_name: str) -> str:

        with self.db_connection(self.database_path) as connection:
            try:
                rename_query = """UPDATE profiles SET unique_profile_name=? WHERE profile_id=?"""
                connection.cursor().execute(rename_query, (new_name, profile_id))
                connection.commit()
                return None
            except sqlite3.IntegrityError:
                return "The profile name you provided already exists. Please choose a different name."
            except sqlite3.OperationalError:
                return "There was an issue processing your request. Please try again later."
            except sqlite3.InterfaceError:
                return "Invalid data provided. Please ensure you're entering the correct information."
            except sqlite3.DatabaseError:
                return "Unexpected database issue. Please try again later."
            except Exception as e:
                return "An unexpected error occurred. Please try again later."

    def add_new_profile(
        self,
        profile_identifier: str,
        profile_name: str,
        x_1: int,
        x_2: int,
        y_1: int,
        y_2: int,
        email_profile_name: str=None,
    ):
        with self.db_connection(self.database_path) as connection:
            add_data = """INSERT INTO profiles(profile_identifier_text, unique_profile_name, x_1, x_2, y_1, y_2, email_profile_name) VALUES(?,?,?,?,?,?,?)"""
            data = (profile_identifier, profile_name, x_1, x_2, y_1, y_2, email_profile_name)
            connection.cursor().execute(add_data, data)
            connection.commit()

    def fetch_profile_id_by_profile_name(self, profile_name: str) -> int:
        with self.db_connection(self.database_path) as connection:
            file_profile_id_query = (
                """SELECT profile_id FROM profiles WHERE unique_profile_name=?"""
            )
            file_profile_data = (
                connection.cursor()
                .execute(file_profile_id_query, (profile_name,))
                .fetchone()
            )
            if file_profile_data is None:
                file_profile_id = None
            else:
                file_profile_id = file_profile_data[0]
        return file_profile_id

    def fetch_profile_description_by_profile_id(self, profile_id: int) -> str:
        with self.db_connection(self.database_path) as connection:
            file_profile_description_query = (
                """SELECT unique_profile_name FROM profiles WHERE profile_id=?"""
            )
            file_profile_data = (
                connection.cursor()
                .execute(file_profile_description_query, (profile_id,))
                .fetchone()
            )
            file_profile_description = file_profile_data[0]
        return file_profile_description

    def fetch_project_description_by_project_number(self, project_number: str) -> str:
        with self.db_connection(self.database_path) as connection:
            project_description_query = (
                """SELECT description FROM project_data WHERE project_number=?"""
            )
            project_description = (
                connection.cursor()
                .execute(project_description_query, (project_number,))
                .fetchone()
            )
            if project_description:
                return project_description[0]
            return ""

    def fetch_project_description_example(self) -> str:
        query = """SELECT description
                FROM project_data
                WHERE description IS NOT NULL AND description != ''
                LIMIT 1;"""
        
        with self.db_connection(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            data = connection.cursor().execute(query).fetchone()
        
        if data:
            return data['description']
        else:
            return ''

    def fetch_active_parameters_by_profile_id(self, profile_id: int) -> list[str]:
        """Get active parameters for a file_profile

        Args:
            file_profile_name (str): unique file profile name

        Returns:
            tuple: Format ([(parameter_id, description, example_text)], file_naming_scheme)
        """
        with self.db_connection(self.database_path) as connection:
            try:
                active_params_query = (
                    """SELECT description FROM profile_parameters WHERE profile_id=?"""
                )
                active_params = (
                    connection.cursor()
                    .execute(active_params_query, (profile_id,))
                    .fetchall()
                )
                active_params = [param[0] for param in active_params]
                if "project_number" in active_params:
                    active_params = ["doc_num", "project_description"] + active_params
                else:
                    active_params = ["doc_num"] + active_params

                return active_params
            except (TypeError, sqlite3.DatabaseError) as e:
                return []
        
    def fetch_secondary_parameter_by_parameter_id(self, parameter_id: int) -> list[str]:
        with self.db_connection(self.database_path) as connection:
            try:
                secondary_params_query = (
                    """SELECT x_1, x_2, y_1, y_2, advanced, comparison_type FROM secondary_profile_parameters WHERE parameter_id=?"""
                )
                secondary_params = (
                    connection.cursor()
                    .execute(secondary_params_query, (parameter_id,))
                    .fetchone()
                )

                return secondary_params

            except (TypeError, sqlite3.DatabaseError) as e:
                return []

    def update_profile_used_count_by_profile_id(self, profile_id: int) -> None:
        with self.db_connection(self.database_path) as connection:
            update_query = """UPDATE profiles SET count=(SELECT count FROM profiles WHERE profile_id=?)+1 WHERE profile_id=?;"""
            connection.cursor().execute(update_query, (profile_id, profile_id))
            connection.commit()

    def fetch_project_directory_by_project_number(self, project_number: str) -> str:
        with self.db_connection(self.database_path) as connection:
            try:
                directory_select_query = (
                    """SELECT directory FROM project_data WHERE project_number=?;"""
                )
                rename_path_project_dir = (
                    connection.cursor()
                    .execute(directory_select_query, (project_number,))
                    .fetchone()
                )
                rename_path_project_dir = rename_path_project_dir[0]
                return rename_path_project_dir
            except (TypeError, sqlite3.DatabaseError) as e:
                return ""

    def fetch_parameter_example_text_by_name_and_profile_id(
        self, profile_id: int, parameter: str
    ) -> str:
        with self.db_connection(self.database_path) as connection:
            try:
                example_text_query = """SELECT example_text FROM profile_parameters WHERE profile_id=? AND description=?"""
                example_text = (
                    connection.cursor()
                    .execute(example_text_query, (profile_id, parameter))
                    .fetchone()
                )
                if example_text:
                    return example_text[0]
                return ""
            except (TypeError, sqlite3.DatabaseError) as e:
                return ""

    def fetch_all_parameter_rectangles_and_description_by_primary_profile_id(self, profile_id: int) -> list[dict]:
        select_rects = """
            SELECT 
                profile_parameters.parameter_id, 
                profile_parameters.description AS primary_description, 
                profile_parameters.x_1 AS primary_x_1, 
                profile_parameters.x_2 AS primary_x_2, 
                profile_parameters.y_1 AS primary_y_1, 
                profile_parameters.y_2 AS primary_y_2, 
                profile_parameters.example_text, 
                profile_parameters.advanced AS primary_advanced,
                secondary_profile_parameters.description AS secondary_description, 
                secondary_profile_parameters.x_1 AS secondary_x_1, 
                secondary_profile_parameters.x_2 AS secondary_x_2, 
                secondary_profile_parameters.y_1 AS secondary_y_1, 
                secondary_profile_parameters.y_2 AS secondary_y_2, 
                secondary_profile_parameters.advanced AS secondary_advanced, 
                secondary_profile_parameters.comparison_type
            FROM profile_parameters
            LEFT JOIN secondary_profile_parameters ON profile_parameters.parameter_id = secondary_profile_parameters.parameter_id
            WHERE profile_parameters.profile_id = ?
        """
        
        with self.db_connection(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            raw_data = connection.cursor().execute(select_rects, (profile_id,)).fetchall()
            
        # Process the data into the desired dictionary format
        processed_data = []
        for row in raw_data:
            processed_data.append({
                'primary': {
                    'coords': (row['primary_x_1'], row['primary_x_2'], row['primary_y_1'], row['primary_y_2']),
                    'description': row['primary_description'],
                    'example_text': row['example_text'],
                    'advanced': row['primary_advanced']
                },
                'secondary': {
                    'coords': (row['secondary_x_1'], row['secondary_x_2'], row['secondary_y_1'], row['secondary_y_2']) if row['secondary_x_1'] else None,
                    'description': row['secondary_description'] if row['secondary_description'] else None,
                    'advanced': row['secondary_advanced'] if row['secondary_advanced'] else None,
                    'comparison_type': row['comparison_type'] if row['comparison_type'] else None
                }
            })
            
        return processed_data

    def fetch_profile_rectangle_by_profile_id(self, profile_id: int) -> list[str]:
        rects_profile_data = []
        with self.db_connection(self.database_path) as connection:
            select_profile_rect = """SELECT x_1, x_2, y_1, y_2, unique_profile_name FROM profiles WHERE profile_id=?;"""
            rects_profile_data = (
                connection.cursor()
                .execute(select_profile_rect, (profile_id,))
                .fetchone()
            )
        return rects_profile_data
    
    def fetch_advanced_option_by_parameter_name_and_profile_id(self, profile_id: int, parameter_name: str) -> str:
        with self.db_connection(self.database_path) as connection:
            advanced_option_query = """SELECT advanced FROM profile_parameters WHERE profile_id=? AND description=?"""
            advanced_option = (
                connection.cursor()
                .execute(advanced_option_query, (profile_id, parameter_name))
                .fetchone()
            )
            if advanced_option and advanced_option[0] is not None:
                return advanced_option[0]
            return ""

    def fetch_parameter_id_by_name(self, profile_id: int, parameter_name: str) -> int:
        with self.db_connection(self.database_path) as connection:
            parameter_query = """SELECT parameter_id FROM profile_parameters WHERE profile_id=? AND description=?;"""
            parameter_data = (profile_id, parameter_name)
            parameter_id = (
                connection.cursor().execute(parameter_query, parameter_data).fetchone()
            )
        if parameter_id is not None:
            parameter_id = parameter_id[0]
        return parameter_id

    def add_new_parameter(
        self,
        profile_id: int,
        parameter_name: str,
        regex: str,
        x_1: int,
        x_2: int,
        y_1: int,
        y_2: int,
        example: str,
        advanced_option: str,
    ):
        with self.db_connection(self.database_path) as connection:
            add_parameter_query = """INSERT INTO profile_parameters(profile_id, description, regex, x_1, x_2, y_1, y_2, example_text, advanced) VALUES(?,?,?,?,?,?,?,?,?)"""
            data = (
                profile_id,
                parameter_name,
                regex,
                x_1,
                x_2,
                y_1,
                y_2,
                example,
                advanced_option
            )
            connection.cursor().execute(add_parameter_query, data)
            connection.commit()

    def add_new_secondary_parameter(self, parameter_id: int, parameter_name: str, x_1: int, x_2: int, y_1: int, y_2: int, advanced_option: str, comparison_type: str):
        with self.db_connection(self.database_path) as connection:
            add_parameter_query = """INSERT INTO secondary_profile_parameters(parameter_id, description, x_1, x_2, y_1, y_2, advanced, comparison_type) VALUES(?,?,?,?,?,?,?,?)"""
            data = (
                parameter_id,
                parameter_name,
                x_1,
                x_2,
                y_1,
                y_2,
                advanced_option,
                comparison_type
            )
            connection.cursor().execute(add_parameter_query, data)
            connection.commit()

    def fetch_all_file_profiles(self, order_by: str) -> list[str]:
        """Fetches the file_profile data to display to user in dropdowns

        Returns:
            list: Profile names
        """
        with self.db_connection(self.database_path) as connection:
            if order_by is None:
                file_profiles_query = """SELECT * FROM profiles"""
            else:
                file_profiles_query = (
                    f"""SELECT * FROM profiles ORDER BY {order_by} DESC"""
                )
            profiles = connection.cursor().execute(file_profiles_query).fetchall()
        if not profiles:
            return []
        return profiles

    def fetch_profile_file_name_pattern_by_profile_id(self, profile_id: str) -> str:
        with self.db_connection(self.database_path) as connection:
            profile_file_name_scheme_query = (
                """SELECT file_naming_format FROM profiles WHERE profile_id = ?"""
            )
            file_name_scheme = (
                connection.cursor()
                .execute(profile_file_name_scheme_query, (profile_id,))
                .fetchone()
            )
        if file_name_scheme:
            return file_name_scheme[0]
        return ""

    def update_template_profile_file_name_pattern(self, profile_name, pattern):
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

    def fetch_all_project_numbers(self) -> list[str]:
        with self.db_connection(self.database_path) as connection:
            project_numbers_query = """SELECT project_number FROM project_data;"""
            project_numbers = (
                connection.cursor().execute(project_numbers_query).fetchall()
            )
        if project_numbers:
            project_numbers = [project_number[0] for project_number in project_numbers]
        return project_numbers

    def fetch_all_project_directories(self) -> list[str]:
        with self.db_connection(self.database_path) as connection:
            project_directories_query = """SELECT directory FROM project_data;"""
            project_directories = (
                connection.cursor().execute(project_directories_query).fetchall()
            )
        if project_directories:
            project_directories = [
                project_directory[0] for project_directory in project_directories
            ]
        return project_directories

    def fetch_project_data_table_headers(self) -> list[str]:
        """Fetches all database headers from project data table"""
        headers = None
        with self.db_connection(self.database_path) as connection:
            # Probably not proper way to mitigate SQL injections but good enough since database_table string is not user supplied
            query = f"""SELECT project_number, directory, description, email_to, email_cc, email_bcc, email_subject, email_profile_name FROM project_data;"""
            try:
                cursor = connection.cursor()
                results = cursor.execute(query).fetchone()
                if results:
                    headers = [x[0] for x in cursor.description]
                else:
                    headers = []
            except sqlite3.DatabaseError as e:
                print(e)
            finally:
                cursor.close()

        return headers

    def fetch_all_project_data(self) -> list[str]:
        """Fetches all database results from project data table"""

        with self.db_connection(self.database_path) as connection:
            # Probably not proper way to mitigate SQL injections but good enough since database_table string is not user supplied
            query = f"""SELECT project_number, directory, description, email_to, email_cc, email_bcc, email_subject, email_profile_name FROM project_data;"""
            try:
                database_fetch_results = connection.cursor().execute(query).fetchall()
                if not database_fetch_results:
                    database_fetch_results = []
            except sqlite3.DatabaseError as e:
                print(e)

        return database_fetch_results
    
    def fetch_project_data_by_project_number(self, project_number: str) -> list[str]:
        """Fetches all database results from project data table"""

        with self.db_connection(self.database_path) as connection:

            query = f"""SELECT project_number, directory, description, email_to, email_cc, email_bcc, email_subject, email_profile_name FROM project_data WHERE project_number=?;"""
            try:
                database_fetch_results = connection.cursor().execute(query, (project_number,)).fetchone()
                if not database_fetch_results:
                    database_fetch_results = []
            except sqlite3.DatabaseError as e:
                print(e)

        return database_fetch_results

    def fetch_all_table_names(self):
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

    def delete_project_data_entry_by_project_number(self, project_number: str) -> str:
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

    def fetch_parameter_rectangle_by_name_and_profile_id(
        self, profile_id: int, parameter_name: str
    ) -> list[int]:
        with self.db_connection(self.database_path) as connection:
            parameter_rectangle_query = """SELECT x_1, x_2, y_1, y_2 FROM profile_parameters WHERE profile_id=? AND description=?;"""
            profile_rectangle = (
                connection.cursor()
                .execute(parameter_rectangle_query, (profile_id, parameter_name))
                .fetchone()
            )

        return profile_rectangle

    def fetch_parameter_regex_by_parameter_name_and_profile_id(
        self, profile_id: int, parameter_name: str
    ) -> str:
        with self.db_connection(self.database_path) as connection:
            parameter_regex_query = """SELECT regex FROM profile_parameters WHERE profile_id=? AND description=?;"""
            profile_regex = (
                connection.cursor()
                .execute(parameter_regex_query, (profile_id, parameter_name))
                .fetchone()
            )
        if profile_regex:
            return profile_regex[0]
        return ""

    def update_project_data_entry(self, old_data, new_data):
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                update_statement = """UPDATE project_data SET project_number=?, directory=?, description=?, email_to=?, email_cc=?, email_bcc=?, email_subject=?, email_profile_name=? WHERE project_number=?;"""
                data = [
                    new_data[key]
                    for key in [
                        "project_number",
                        "directory",
                        "description",
                        "email_to",
                        "email_cc",
                        "email_bcc",
                        "email_subject",
                        "email_profile_name",
                    ]
                ]
                data.append(old_data["project_number"])
                connection.cursor().execute(update_statement, data)
                connection.commit()
            except Exception as e:
                msg = f"Error updating Project Data: {e}"

        return msg

    def add_new_project_data(self, new_data: dict) -> str:
        """Adds new project data to database"""
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                new_data_query = """INSERT INTO project_data (project_number,directory,description,email_to,email_cc,email_bcc,email_subject,email_profile_name) VALUES(?,?,?,?,?,?,?,?);"""
                data = [
                    new_data[key]
                    for key in [
                        "project_number",
                        "directory",
                        "description",
                        "email_to",
                        "email_cc",
                        "email_bcc",
                        "email_subject",
                        "email_profile_name",
                    ]
                ]
                connection.cursor().execute(new_data_query, data)
                connection.commit()
            except Exception as e:
                msg = f"{e}"

        return msg

    def export_project_data_thread(self, export_location):
        self.progress_popup = loading_widget.LoadingWidget(
            title="Exporting", text="Exporting Project Data..."
        )
        self.export_data_thread = ExportProjectDataThread(
            export_location=export_location,
            db_connection=self.db_connection,
            database_path=self.database_path,
            export_progress=self.export_progress,
            export_result=self.export_result,
        )

        self.export_progress.connect(self.update_progress_widget)
        self._thread_pool.start(self.export_data_thread)

    def import_project_data_thread(self, project_data: list[str]):
        self.progress_popup = loading_widget.LoadingWidget(
            title="Importing", text="Importing Project Data..."
        )
        self.import_data_thread = ImportProjectDataThread(
            project_data=project_data,
            db_connection=self.db_connection,
            database_path=self.database_path,
            import_progress=self.import_progress,
            import_result=self.import_result,
        )

        self.import_progress.connect(self.update_progress_widget)
        self._thread_pool.start(self.import_data_thread)

    def delete_all_project_data_thread(self):
        self.progress_popup = loading_widget.LoadingWidget(
            title="Deleting", text="Deleting Project Data..."
        )
        self.delete_data_thread = DeleteProjectDataThread(
            db_connection=self.db_connection,
            database_path=self.database_path,
            delete_progress=self.delete_progress,
            delete_result=self.delete_result,
        )

        self.delete_progress.connect(self.update_progress_widget)
        self._thread_pool.start(self.delete_data_thread)

    def update_progress_widget(self, value: int):
        self.progress_popup.update_val(value=value)

    def fetch_email_profile_name_by_profile_id(self, profile_id: int) -> str:
        with self.db_connection(self.database_path) as connection:
            profile_query = """SELECT email_profile_name FROM profiles WHERE profile_id=?;"""
            profile_data = (
                connection.cursor().execute(profile_query, (profile_id,)).fetchone()
            )
        if profile_data:
            profile_data = profile_data[0]
        else:
            profile_data = ""
        return profile_data
    
    def fetch_email_profile_name_by_project_number(self, project_number: str) -> str:
        with self.db_connection(self.database_path) as connection:
            profile_query = """SELECT email_profile_name FROM project_data WHERE project_number=?;"""
            profile_data = (
                connection.cursor().execute(profile_query, (project_number,)).fetchone()
            )
        if profile_data:
            profile_data = profile_data[0]
        else:
            profile_data = ""
        return profile_data
    
    def update_email_profile_by_profile_id(self, profile_id: int, email_profile_name: str):
        with self.db_connection(self.database_path) as connection:
            profile_query = """UPDATE profiles SET email_profile_name=? WHERE profile_id=?;"""
            connection.cursor().execute(profile_query, (email_profile_name, profile_id))
            connection.commit()
        return
    
    def update_email_profile_by_project_id(self, project_id: int, email_profile_name: str):
        with self.db_connection(self.database_path) as connection:
            profile_query = """UPDATE project_data SET email_profile_name=? WHERE id=?;"""
            connection.cursor().execute(profile_query, (email_profile_name, project_id))
            connection.commit()
        return
    
    def fetch_email_template_info_by_email_template_name(self, email_template_name: str) -> list[str]:
        with self.db_connection(self.database_path) as connection:
            profile_query = """SELECT email_subject, email_body FROM email_templates WHERE email_template_name=?;"""
            profile_data = (
                connection.cursor().execute(profile_query, (email_template_name,)).fetchone()
            )
        if profile_data:
            profile_data = profile_data
        else:
            profile_data = []
        return profile_data


class ImportProjectDataThread(QtCore.QRunnable):
    def __init__(
        self,
        project_data: list[str],
        db_connection: typing.Callable,
        database_path: str,
        import_result: QtCore.Signal,
        import_progress: QtCore.Signal,
    ):
        super(ImportProjectDataThread, self).__init__()
        self.db_connection = db_connection
        self.import_project_data = project_data
        self.database_path = database_path
        self.result_signal = import_result
        self.progress_signal = import_progress
        self._progress = 0
        self._result = None

    @QtCore.Slot()
    def run(self):
        # debugpy.debug_this_thread()
        msg = None
        try:
            progress = 33
            with self.db_connection(self.database_path) as connection:
                results = (
                    connection.cursor()
                    .execute("""SELECT project_number FROM project_data;""")
                    .fetchall()
                )
            result_list = []
            for i, result in enumerate(results):
                result_list.append(result[0])
                self._progress = int((1 + i) / len(results) * progress)
                try:
                    self.progress_signal.emit(self._progress)
                except Exception as e:
                    print(e)
                    pass

            # Remove non-unique project numbers before importing
            # Removing them now and using executemany was WAY faster than not removing duplicates and using execute to insert rows individually
            # and letting unique constraint just go to exception
            temp_project_data = []
            for i, project in enumerate(self.import_project_data):
                self.temp_progress = int(
                    (1 + i) / len(self.import_project_data) * progress
                )
                self.progress_signal.emit(self._progress + self.temp_progress)
                if project[0] not in result_list:
                    temp_project_data.append(project)
            self._progress = self._progress + self.temp_progress
            self.import_project_data = temp_project_data
            with self.db_connection(self.database_path) as connection:
                msg = connection.cursor().executemany(
                    """INSERT INTO project_data (project_number,directory,description,email_to,email_cc,email_bcc,email_subject,email_profile_name) VALUES(?,?,?,?,?,?,?,?);""",
                    self.import_project_data,
                )
                connection.commit()
            self._progress = 99
            self.progress_signal.emit(self._progress)
        except Exception as e:
            msg = f"Error: {e}"
        finally:
            self._result = msg
            self.result_signal.emit(self._result)
            self._progress = 100
            self.progress_signal.emit(self._progress)

    @property
    def progress(self):
        return self._progress

    @property
    def result(self):
        return self._result


class ExportProjectDataThread(QtCore.QRunnable):
    def __init__(
        self,
        export_location: str,
        export_result: QtCore.Signal, 
        export_progress: QtCore.Signal,
        db_connection: typing.Callable,
        database_path: str,
    ):
        super(ExportProjectDataThread, self).__init__()
        self.result_signal = export_result
        self.progress_signal = export_progress
        self.export_location = export_location
        self.db_connection = db_connection
        self.database_path = database_path
        self._progress = 0
        self._result = None

    @QtCore.Slot()
    def run(self):
        msg = None
        try:
            with self.db_connection(self.database_path) as connection:

                cursor = connection.cursor()

                results = cursor.execute("SELECT * FROM project_data;").fetchall()
                results = [result[1:] for result in results]  # remove id column

                headers = [i[0] for i in cursor.description]
                headers = headers[1:]

            self._progress = 25
            self.progress_signal.emit(self._progress)
            with open(
                os.path.abspath(os.path.join(self.export_location)),
                "w",
                newline="",
            ) as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(headers)  # write headers
                self._progress = 70
                self.progress_signal.emit(self._progress)
                csv_writer.writerows(results)
        except Exception as e:
            msg = f"Error: {e}"
            print(e)
        finally:
            self._result = msg
            self.result_signal.emit(self._result)
            self._progress = 100
            self.progress_signal.emit(self._progress)


class DeleteProjectDataThread(QtCore.QRunnable):
    def __init__(
        self,
        delete_result: QtCore.Signal, 
        delete_progress: QtCore.Signal,
        db_connection: typing.Callable,
        database_path: str,
    ):
        super(DeleteProjectDataThread, self).__init__()
        self.result_signal = delete_result
        self.progress_signal = delete_progress
        self.db_connection = db_connection
        self.database_path = database_path

    @QtCore.Slot()
    def run(self):
        msg = None
        with self.db_connection(self.database_path) as connection:
            try:
                self.progress_signal.emit(50)
                connection.cursor().execute("""DELETE FROM project_data;""")
                connection.commit()
            except Exception as e:
                msg = f"Error: {e}"
            finally:
                self.progress_signal.emit(100)
                self.result_signal.emit([msg])
