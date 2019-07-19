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

# SQLITE DB

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

def setup_output_db(cursor):
	add_json_to_output_db()
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS ezproxy_doi 
		(ezproxy_doi_id INTEGER PRIMARY KEY, title TEXT, doi TEXT, doi_link TEXT, doi_response JSON, pdf_link TEXT, xml_link TEXT, unspecified_link TEXT)''')

# MYSQL DB

def setup_ezproxy_spu_table(cursor):
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS `ezproxy_spu_doi` (
  		`id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  		`datetime` datetime DEFAULT NULL,
  		`ip` varchar(50) DEFAULT NULL,
  		`session` varchar(100) DEFAULT NULL,
  		`web` varchar(255) DEFAULT NULL,
  		`address` varchar(1000) DEFAULT NULL,
  		`ptype` varchar(100) DEFAULT NULL,
  		`ezproxy_doi_id` int(11) DEFAULT NULL,
  		PRIMARY KEY (`id`)
		) ENGINE=InnoDB AUTO_INCREMENT=351449 DEFAULT CHARSET=utf8;
	''')

def setup_ezproxy_items_table(cursor):
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS `ezproxy_doi_items` (
  		`id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  		`title` varchar(1000) DEFAULT NULL,
  		`doi` varchar(255) DEFAULT NULL,
  		`doi_link` varchar(1000) DEFAULT NULL,
  		PRIMARY KEY (`id`)
		) ENGINE=InnoDB AUTO_INCREMENT=351449 DEFAULT CHARSET=utf8;
	''')

def setup_ezproxy_db(cursor):
	setup_ezproxy_spu_table(cursor)
	setup_ezproxy_items_table(cursor)
	# cursor.execute('''
	# 	CREATE TABLE IF NOT EXISTS ezproxy_subjects
	# ''')
	# sqlite_cursor.execute("CREATE TABLE IF NOT EXISTS subjects (subject_id INTEGER PRIMARY KEY, subject TEXT)")
	# sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS doi_subjects 
	# 		(ezproxy_doi_id INTEGER, subject_id INTEGER, FOREIGN KEY(ezproxy_doi_id) REFERENCES ezproxy_doi(ezproxy_doi_id), FOREIGN KEY(subject_id) REFERENCES subjects(subject_id))''')


# CREATE TABLE ezproxy_spu_doi LIKE ezporxy_spu; 
# INSERT ezproxy_spu_doi SELECT * FROM ezporxy_spu;

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