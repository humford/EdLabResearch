# Import Configuration
from config import config

ezproxy_db = config["DATABASES"]["EZPROXY_DB"]
library_sierra_db = config["DATABASES"]["LIBRARY_SIERRA_DB"]
output_dir = config["OUTPUT"]["DIRECTORY"]
output_db = config["OUTPUT"]["DATABASE"]

# Import Internal

# Import External
import sqlite3
import json
import mysql.connector

# MAIN
def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def add_json_to_output_db():
	sqlite3.register_adapter(dict, adapt_json)
	sqlite3.register_adapter(list, adapt_json)
	sqlite3.register_adapter(tuple, adapt_json)
	sqlite3.register_converter('JSON', convert_json)

def connect_to_output_db():
	return sqlite3.connect(output_dir + output_db)

def connect_to_ezproxy_db():
	ezproxy_conn = mysql.connector.connect(
		host = ezproxy_db["HOST"],
		user = ezproxy_db["USER"],
		passwd = ezproxy_db["PASSWD"],
		database = ezproxy_db["DATABASE"]
	)
	return ezproxy_conn

def connect_to_sierra_db():
	sierra_conn = mysql.connector.connect(
		host = library_sierra_db["HOST"],
		user = library_sierra_db["USER"],
		passwd = library_sierra_db["PASSWD"],
		database = library_sierra_db["DATABASE"]
	)
	return sierra_conn

# conn = connect_to_ezproxy_db()
# sqlite_cursor = conn.cursor()
# sqlite_cursor.execute("SELECT * FROM ezporxy_spu")
# print(sqlite_cursor.fetchall())