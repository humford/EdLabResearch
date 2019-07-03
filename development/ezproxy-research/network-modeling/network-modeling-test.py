import sqlite3
from crossref.restful import Works, Prefixes, Journals
from habanero import Crossref
from pprint import pprint
from requests.exceptions import HTTPError

cr = Crossref(mailto = "htw2116@columbia.edu")

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def build_graph(data):
	pass

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("../ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

journals = Journals()
works = Works()

sqlite_cursor.execute("SELECT doi FROM ezproxy_doi WHERE doi IS NOT NULL")
DOIs = sqlite_cursor.fetchall()

#print(DOIs)

# a = cr.journals()

for item in DOIs:
	DOI = item[0]
	print("running..." + DOI)
	try:
		journals = cr.journals(ids = cr.works(ids=DOI)["message"]["ISSN"])
		if "message" in journals:
			pass
		elif type(journals) == type(list()):
			journals = journals[0]
		else:
			continue
		#print(journals)
		print("Journal Title: " + journals["message"]["title"])
		print("Subjects: " + str(journals["message"]["subjects"]))
	except HTTPError:
		print("HTTPError")
		continue