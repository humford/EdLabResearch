import json
import requests
import pprint
import sqlite3
import os

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def info_from_DOI(DOI):
	return requests.get("https://doi.org/" + DOI, headers = {"Accept":"application/vnd.citationstyles.csl+json"}).json()

def add_link_columns(sqlite_cursor):
	sqlite_cursor.execute("ALTER TABLE ezproxy_doi ADD COLUMN pdf_link TEXT DEFAULT NULL")
	sqlite_cursor.execute("ALTER TABLE ezproxy_doi ADD COLUMN xml_link TEXT DEFAULT NULL")
	sqlite_cursor.execute("ALTER TABLE ezproxy_doi ADD COLUMN unspecified_link TEXT DEFAULT NULL")
	return

def get_DOI_links(DOI):
	links = {"application/pdf" : None, "application/xml" : None, "unspecified" : None}
	found = False
	while not found:	
		try:
			response = info_from_doi(DOI)
			if response:
				found = True
		except json.decoder.JSONDecodeError:
			if requests.get("https://doi.org/" + DOI, headers = {"Accept":"application/vnd.citationstyles.csl+json"}).content == "Resource not found.":
				continue
			else:
				print("Not found on doi.org")
				return links
	if "link" in response.keys():
		for item in response["link"]:
			if item["content-type"] == "application/pdf":
				links["application/pdf"] = item["URL"]
			elif item["content-type"] == "application/xml":
				links["application/xml"] = item["URL"]
			elif item["content-type"] == "unspecified":
				links["unspecified"] = item["URL"]
	return links

def add_DOI_links(sqlite_cursor):
	sqlite_cursor.execute("SELECT * FROM ezproxy_doi")
	data = sqlite_cursor.fetchall()

	for item in data:
		ezproxy_doi_id = item[0]
		DOI = item[2]
		if not DOI:
			print(f"Skipped {ezproxy_doi_id} of {len(data)}")
			continue
		if item[5] or item[6] or item[7]:
			print(f"Skipped {ezproxy_doi_id} of {len(data)}")
			continue
		links = get_DOI_links(DOI)
		print(links)
		sqlite_cursor.execute("UPDATE ezproxy_doi SET pdf_link = ? WHERE ezproxy_doi_id = ?", (links["application/pdf"], ezproxy_doi_id))
		sqlite_cursor.execute("UPDATE ezproxy_doi SET xml_link = ? WHERE ezproxy_doi_id = ?", (links["application/xml"], ezproxy_doi_id))
		sqlite_cursor.execute("UPDATE ezproxy_doi SET unspecified_link = ? WHERE ezproxy_doi_id = ?", (links["application/pdf"], ezproxy_doi_id))
		print(f"Inserted {ezproxy_doi_id} of {len(data)}")
	return

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

#add_link_columns(sqlite_cursor)

sqlite_cursor.execute("SELECT * FROM ezproxy_doi")
#sqlite_cursor.execute("SELECT * FROM ezproxy_doi WHERE doi = ?", ("10.1177/0049124113500475",))
data = sqlite_cursor.fetchall()

add_DOI_links(sqlite_cursor)

print("Saving database...")
conn.commit()
conn.close()
print("Saved")

#folder_location = r'pdf'
#if not os.path.exists(folder_location):os.mkdir(folder_location)

# for item in data:
# 	if item[0]:
# 		link = DOI_links(item[0])
# 		if link:
# 			filename = os.path.join(folder_location,"".join(i for i in item[0] if i.isalnum()))
# 			if filename[-4:] != ".pdf":
# 				filename = filename + ".pdf"
# 			with open(filename, 'wb+') as f:
# 				f.write(requests.get(link, allow_redirects=True).content)