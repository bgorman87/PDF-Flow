from functions.data_handler import db_connect, db_disconnect, db_file_path
import os, json
import sqlite3
# 
# connection, cursor = db_connect(db_file_path)

database_path = os.path.join(
            os.getcwd(), "database", "db.sqlite3")

# add_data = """INSERT INTO profiles(profile_identifier_text, x_1, x_2, y_1, y_2) VALUES(?,?,?,?,?)"""
# data = [("placement", 550, 1150, 175, 225)]

# for data_entry in data:
#     try:
#         cursor.execute(add_data, data_entry)
#         connection.commit()
#     except sqlite3.IntegrityError as e:
#         # print(f"Error inserting data: {e}")
#         pass

# db_disconnect(connection, cursor)
# connection, cursor = db_connect(db_file_path)

# add_data = """INSERT INTO profile_paramaters(profile_id,
#             description,
#             x_1,
#             x_2,
#             y_1,
#             y_2)
#             VALUES(?,?,?,?,?,?);"""

# data = [["lacement", "project number", 380, 660, 310, 340],
#         ["lacement", "date placed", 1280, 1420, 645, 680],
#         ["testreport", "project number", 1150, 1475, 315, 350],
#         ["testreport", "set number", 250, 350, 630, 670],
#         ["testreport", "date cast", 1270, 1450, 630, 670],
#         ["testreport", "break strengths", 1200, 1320, 760, 1200],
#         ["testreport", "break ages", 400, 475, 760, 1200],
#         ["density", "project number", 1050, 1550, 290, 350],
#         ["density", "date placed", 300, 475, 660, 725]
#         ]

# for i, data_entry in enumerate(data):
#     file_id_select = """SELECT profile_id FROM profiles WHERE profile_identifier_text = ?;"""
#     profile_id = cursor.execute(file_id_select, (data_entry[0],))
#     data[i][0] = file_id.fetchone()[0]

# for data_entry in data:
#     try:
#         cursor.execute(add_data, data_entry)
#         connection.commit()
#     except sqlite3.IntegrityError as e:
#         # print(f"Error inserting data: {e}")
#         pass

# connection, cursor = db_connect(db_file_path)
# data_update = "UPDATE profile_paramaters SET regex='(\d{2}[\s-]+[A-z]{3}[\s-]\d{2})' WHERE profile_id='3' and description='date placed';"
# cursor.execute(data_update)
# connection.commit()
# db_disconnect(connection, cursor)

# connection, cursor = db_connect(db_file_path)
# data_update = "UPDATE profiles SET x_1=760, x_2=1000, y_1=170, y_2=230 WHERE profile_id='4';"
# cursor.execute(data_update)
# connection.commit()
# db_disconnect(connection, cursor)

# cursor.executemany(add_data, data)
# connection.commit()

# connection, cursor = db_connect(db_file_path)
# projects_initialization = """CREATE TABLE IF NOT EXISTS project_data (
#                         id INTEGER PRIMARY KEY,
#                         project_number TEXT UNIQUE NOT NULL,
#                         directory TEXT NOT NULL,
#                         email_to TEXT NOT NULL,
#                         email_cc TEXT,
#                         email_bcc TEXT,
#                         email_subject TEXT NOT NULL
#                         );"""
# cursor.execute(projects_initialization)
# connection.commit()
# db_disconnect(connection, cursor)

# cwd = os.getcwd()
# json_filename = os.path.join(cwd, "sorter_data.json")
# print(json_filename)

# json_projects = {}

# # Read JSON data into the data_store variable
# if json_filename:
#     with open(json_filename, 'r') as f:
#         data_store = json.load(f)
# project_directory = r"B:\Documents\Programming\GitHub\modular_report_sorter\test project dir"
# connection, cursor = db_connect(db_file_path)
# insert_query = """INSERT INTO project_data (project_number, directory, email_to, email_cc, email_subject) VALUES (?,?,?,?,?)"""
# data_keys = ["project_number", "project_directory", "project_email_to", "project_email_cc", "project_email_subject"]
# for item in data_store:
#     data = []
#     for key in data_keys:
#         data.append(item[key])
#     data[1] = project_directory
#     try:
#         cursor.execute(insert_query, data)
#         connection.commit()
#     except Exception:
#         # print(data)
#         pass

# db_disconnect(connection, cursor)
import timeit
import csv

# connection, cursor = db_connect(db_file_path)
# try:
#     results = cursor.execute("""SELECT * FROM project_data;""").fetchall()
#     with open("exported.csv", "w", newline="") as csv_file:
#         csv_writer = csv.writer(csv_file)
#         csv_writer.writerow([i[0] for i in cursor.description]) # write headers
#         csv_writer.writerows(results)
# except:
#     pass
# finally:
#     db_disconnect(connection, cursor)

connection, cursor = db_connect(database_path)

cursor.execute(f"""DELETE FROM project_data WHERE project_number LIKE ?""", ('%'+'2102531'+'%',))
connection.commit()
# to_db = []
# try:
#     # cursor = cursor.execute("""SELECT * FROM """)
    
#     with open("exported.csv", "r") as imported_file:
#         import_data = csv.reader(imported_file)
#         for row in import_data:
#             to_db.append(row)
#         # to_db = [(row[item] for item in ['project_number','directory','email_to','email_cc','email_bcc','email_subject']) for row in import_data]
#     to_db = to_db[2:]
#     # start = timeit.default_timer()
#     # for row in to_db:
#     #     cursor.execute("""INSERT INTO project_data (project_number,directory,email_to,email_cc,email_bcc,email_subject) VALUES(?,?,?,?,?,?);""", row)
#     #     connection.commit()
#     # stop = timeit.default_timer()
#     # print('One at a time: ', stop - start)
    
#     # cursor.execute("""DELETE FROM project_data""")
#     # connection.commit()

#     start = timeit.default_timer()

#     # to_db = [project_row for project_row in to_db if not any(project_row[0] in db_row for db_row in results)]        
#     cursor.executemany("""INSERT INTO project_data (project_number,directory,email_to,email_cc,email_bcc,email_subject) VALUES(?,?,?,?,?,?);""", to_db)
#     connection.commit()
#     results = cursor.execute("""SELECT * FROM project_data;""").fetchall()
    
#     stop = timeit.default_timer()
#     print(f"Len db: {len(results)}")
#     print('Bulk: ', stop - start)   
# except Exception as e:
#     print(e)
#     pass
# finally:
db_disconnect(connection, cursor)