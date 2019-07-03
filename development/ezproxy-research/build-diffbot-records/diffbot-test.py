import urllib.parse
import json
import requests
import sqlite3
import mysql.connector
import re

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def get_ezproxy_data(mysql_cursor, web):
	mysql_cursor.execute("SELECT * FROM ezporxy_spu WHERE web = %s", (web,))
	return mysql_cursor.fetchall()

def get_ezproxy_subset(data, regex):
	subset = []
	for entry in data:
		if re.match(regex, entry[5]):
			subset.append(entry)
	return subset

def get_ezproxy_db():
	researchdb = mysql.connector.connect (
		host = "analytics.tc-library.org",
		user = "research",
		passwd = "S@YZfH",
		database = "ezproxy-logs-oclc"
	)
	return researchdb

def setup_output_db(sqlite_cursor):
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS ezproxy_records 
			(record_id INTEGER PRIMARY KEY, address TEXT, diffbot_title TEXT, diffbot_author TEXT, diffbot_sitename TEXT, num_tags INTEGER, diffbot_json JSON)''')
	sqlite_cursor.execute("CREATE TABLE IF NOT EXISTS tags (tag_id INTEGER PRIMARY KEY, label TEXT, uri TEXT)")
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS record_tags 
			(record_id INTEGER, tag_id INTEGER, score REAL, count INTEGER, FOREIGN KEY(record_id) REFERENCES ezproxy_records(record_id), FOREIGN KEY(tag_id) REFERENCES tags(tag_id))''')
	return

def test_diffbot():
	url_to_search = input("URL To Search: ")
	response = get_diffbot_response(url_to_search)
	print(json.dumps(response, indent = 4))

def get_diffbot_response(url_to_search):
	token = "e2076bb55a31ff21b37e787fc50c5bc0"
	encoded_url = urllib.parse.quote(url_to_search)
	api_url = f"https://api.diffbot.com/v3/article?token={token}&url={encoded_url}"
	r = requests.get(api_url)
	return r.json()

def diffbot_process(data, mysql_cursor, sqlite_cursor, OFFSET = 1):
	MAX_INDEX = len(data)

	for i in range(MAX_INDEX):
		entry = data[i]
		ezproxy_id = entry[0]
		record_address = entry[5]

		sqlite_cursor.execute("SELECT record_id FROM ezproxy_records WHERE address = ?", (record_address,))
		cache = sqlite_cursor.fetchone()

		if cache:
			print(f"Found item {cache[0]} in cache.")
			print(f"Finished {int(i) + OFFSET} of {int(MAX_INDEX)}")
			continue
		
		response = get_diffbot_response(record_address)

		try:
			tag_list = response["objects"][0]["tags"]
		except KeyError:
			tag_list = []

		try:
			record_title = response["objects"][0]["title"]
		except KeyError:
			record_title = ""

		try:
			record_author = response["objects"][0]["author"]
		except KeyError:
			record_author = ""

		try:
			record_sitename = response["objects"][0]["siteName"]
		except KeyError:
			record_sitename = ""

		try:
			ezproxy_record = (record_address, record_title, record_author, record_sitename, len(tag_list), response)
			sqlite_cursor.execute("INSERT INTO ezproxy_records VALUES (NULL, ?, ?, ?, ?, ?, ?)", ezproxy_record)
			sqlite_cursor.execute("SELECT last_insert_rowid()")
			record_id = sqlite_cursor.fetchone()[0]
		except Exception as e:
			print(json.dumps(response, indent=4))
			print(e)
			print("Saving database...")
			conn.commit()
			print("Saved")

		if tag_list:
			for tag_info in tag_list:
				score = tag_info["score"]
				count = tag_info["count"]
				label = tag_info["label"]
				uri = tag_info["uri"]

				sqlite_cursor.execute("SELECT tag_id FROM tags WHERE label = ?", (label,))
				try:
					tag_id = sqlite_cursor.fetchone()[0]
				except TypeError:
					sqlite_cursor.execute("INSERT INTO tags VALUES (NULL, ?, ?)", (label, uri))
					sqlite_cursor.execute("SELECT last_insert_rowid()")
					tag_id = sqlite_cursor.fetchone()[0]

				sqlite_cursor.execute("INSERT INTO record_tags VALUES (?, ?, ?, ?)", (record_id, tag_id, score, count))

		print(f"Wrote item {record_id} to database")
		print(f"Finished {int(i) + OFFSET} of {int(MAX_INDEX)}")

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("ezproxy-diffbot.db")
sqlite_cursor = conn.cursor()

setup_output_db(sqlite_cursor)

ezproxy = get_ezproxy_db()
mysql_cursor = ezproxy.cursor()

print(json.dumps(get_diffbot_response(input("URL: "))))

# data = get_ezproxy_subset(get_ezproxy_data(mysql_cursor, "onlinelibrary.wiley.com"), r"^(https:\/\/onlinelibrary\.wiley\.com\/doi\/).*")

# diffbot_process(data, mysql_cursor, sqlite_cursor)

# test_diffbot()

# print("Saving database...")
# conn.commit()
# conn.close()
# print("Saved")