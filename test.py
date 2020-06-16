import sqlite3

db = sqlite3.connect('database.db')
cur = db.cursor()
cur.execute('''CREATE TABLE files (Project TEXT, Date DATE, Type TEXT, Set_No INTEGER, Age INTEGER)''')

db.commit()
