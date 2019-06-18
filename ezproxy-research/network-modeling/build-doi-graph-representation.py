# Get DOIs from ezproxy
import sqlite3

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("../ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

sqlite_cursor.execute("SELECT doi FROM ezproxy_doi WHERE doi IS NOT NULL")
DOIs = [item[0] for item in sqlite_cursor.fetchall()]

# Build a Graph Tools Representation of DOI Metadata Structure
# Need a list of valid DOIs

from graph_tools import *

print(DOIs)