import sqlite3
import json
import re

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("ezproxy-diffbot.db")
sqlite_cursor = conn.cursor()

sqlite_cursor.execute("SELECT * FROM record_tags")
d = sqlite_cursor.fetchall()
for i in d:
	sqlite_cursor.execute("UPDATE record_tags SET tag_id = ? WHERE record_id = ? AND tag_id = ?", (int(re.sub(r"^b'\[(.*)\]'", "\\1", str(i[1]))), i[0],i[1]))
	
conn.commit()
conn.close()
