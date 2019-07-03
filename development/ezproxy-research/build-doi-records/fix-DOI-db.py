import sqlite3
import json
import re

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def setup_output_db(sqlite_cursor):
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS ezproxy_doi 
			(ezproxy_doi_id INTEGER PRIMARY KEY, title TEXT, doi TEXT, doi_link TEXT, doi_response JSON)''')
	return

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

setup_output_db(sqlite_cursor)

sqlite_cursor.execute("SELECT * FROM ezproxy_doi_old")
d = sqlite_cursor.fetchall()
for i in d:
	if not i[2]:
		sqlite_cursor.execute("INSERT INTO ezproxy_doi VALUES (NULL, ?, ?, ?, ?)", (i[1], i[2], i[3], i[4]))
		print("NULL VAL")
	else:
		sqlite_cursor.execute("SELECT * FROM ezproxy_doi WHERE doi = ?", (i[2], ))
		z = sqlite_cursor.fetchone()
		if not z:
			sqlite_cursor.execute("INSERT INTO ezproxy_doi VALUES (NULL, ?, ?, ?, ?)", (i[1], i[2], i[3], i[4]))
			print("ADDED")
		else:
			continue
			print("DUPLICATE")

	
conn.commit()
conn.close()
