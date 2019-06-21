import mysql.connector
import sqlite3

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def get_ezproxy_db():
	researchdb = mysql.connector.connect (
		host = "analytics.tc-library.org",
		user = "research",
		passwd = "S@YZfH",
		database = "ezproxy-logs-oclc"
	)
	return researchdb

def setup_output_db(sqlite_cursor):
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS ezproxy_doi 
		(ezproxy_doi_id INTEGER PRIMARY KEY, title TEXT, doi TEXT, doi_link TEXT, doi_response JSON)''')
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS ezproxy_spu
		(ezproxy_id INTEGER PRIMARY KEY, datetime )''')
	return

def add_subjects_tables(sqlite_cursor):
	sqlite_cursor.execute("CREATE TABLE IF NOT EXISTS subjects (subject_id INTEGER PRIMARY KEY, subject TEXT)")
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS doi_subjects 
			(ezproxy_doi_id INTEGER, subject_id INTEGER, FOREIGN KEY(ezproxy_doi_id) REFERENCES ezproxy_doi(ezproxy_doi_id), FOREIGN KEY(subject_id) REFERENCES subjects(subject_id))''')
	return

def add_records_tables(sqlite_cursor):
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS ezproxy_users
		(ezproxy_user_id INTEGER PRIMARY KEY, uni TEXT''')
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS access_records
		(access_record_id INTEGER PRIMARY KEY, ezproxy_user_id INTEGER, ezproxy_doi_id INTEGER, session TEXT, datetime DATETIME, FOREIGN KEY(ezproxy_user_id) REFERENCES ezproxy_users(ezproxy_user_id), FOREIGN KEY(ezproxy_doi_id) REFERENCES ezproxy_doi(ezproxy_doi_id)''')
	return

def get_access_records(mysql_cursor):
	mysql_cursor.execute("SELECT * FROM ")

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

ezproxy = get_ezproxy_db()
mysql_cursor = ezproxy.cursor()

