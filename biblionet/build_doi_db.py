# Import Configuration
from config import config

output_dir = config["OUTPUT"]["DIRECTORY"]
output_db = config["OUTPUT"]["DATABASE"]
crossref_email = config["API"]["CROSSREF_EMAIL"]

# Import Internal
from db_utils import *
from doi_utils import *

# Import External


# MAIN
def get_DOI_links(data, web_resources):
	DOI_links = {}
	index = 1
	unique = []
	for item in data:
		unique.append(item[0])
	data = list(set(unique))

	for link in data:
		parsed_link = urlparse(link)
		netloc = trim_netloc(parsed_link.netloc)
		convert_function = web_resources.get(netloc, no_convert)
		DOI_link = convert_function(parsed_link)
		DOI_links[link] = DOI_link
		print(f"Link {index} of {len(data)} processed.")
		index += 1
	return DOI_links

def insert_entry(DOI_link, sqlite_cursor):
	try:
		DOI_response = json.dumps(xmltodict.parse(requests.get(DOI_link).content))
	except:
		DOI_response = json.dumps({})

	title = title_from_link(DOI_link)
	DOI = DOI_from_link(DOI_link)

	if DOI:
		sqlite_cursor.execute("SELECT * FROM ezproxy_doi WHERE doi = ?", (DOI, ))
		cache = sqlite_cursor.fetchone()
		if cache:
			print(f"Item {DOI} found in cache.")
			return

	DOI_entry = (title, DOI, DOI_link, DOI_response)
	sqlite_cursor.execute("INSERT INTO ezproxy_doi VALUES (NULL, ?, ?, ?, ?)", DOI_entry)
	print(f"Item {DOI} inserted.")

def convert_all(web_resources, mysql_cursor, sqlite_cursor):
	setup_output_db(sqlite_cursor)

	mysql_cursor.execute("SELECT address FROM ezporxy_spu")
	data = mysql_cursor.fetchall()
	DOI_links = get_DOI_links(data, web_resources)

	index = 1
	for DOI_link in DOI_links.values():
		print(DOI_link)
		if DOI_link:
			insert_entry(DOI_link, sqlite_cursor)
			print(f"Link {index} of {len(DOI_links.values())} processed.")
		else:
			print(f"Link {index} of {len(DOI_links.values())} is blank, skipping.")
		index += 1

	return