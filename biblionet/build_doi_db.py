# Import Configuration
from config import config

output_dir = config["OUTPUT"]["DIRECTORY"]
output_db = config["OUTPUT"]["DATABASE"]
crossref_email = config["API"]["CROSSREF_EMAIL"]

# Import Internal
from db_utils import *
from doi_utils import *

# Import External
from timeit import default_timer as timer

start = timer()
end = timer()
print(f"X takes {end - start} seconds to run.")

# MAIN

# SUBJECTS

# USERS

# BUILDING ENTRIES
def get_DOI_links(data, web_resources):
	DOI_links = {}
	index = 1

	for link in data:
		parsed_link = urlparse(link)
		netloc = trim_netloc(parsed_link.netloc)
		convert_function = web_resources.get(netloc, no_convert)
		DOI_link = convert_function(parsed_link)
		DOI_links[link] = DOI_link
		print(f"Link {index} of {len(data)} processed.")
		index += 1
	return DOI_links

def insert_entry(DOI_link, cursor, mode):
	try:
		DOI_response = json.dumps(xmltodict.parse(requests.get(DOI_link).content))
	except:
		DOI_response = json.dumps({})

	DOI = DOI_from_link(DOI_link)
	links = {"application/pdf" : None, "application/xml" : None, "unspecified" : None}

	if DOI:
		title = title_from_DOI(DOI)
			
		if mode == "sqlite": cursor.execute("SELECT ezproxy_doi_id FROM ezproxy_doi WHERE doi = ?", (DOI, ))
		elif mode == "mysql": cursor.execute("SELECT id FROM ezproxy_doi_items WHERE doi = %s", (DOI, ))
		cache = cursor.fetchone()
		if cache:
			print(f"Item {DOI} found in cache.")
			return cache[0]
	else:
		title = title_from_link(DOI_link)
		
	if mode == "sqlite":
		DOI_entry = (title, DOI, DOI_link, DOI_response, links["application/pdf"], links["application/xml"], links["unspecified"])
		cursor.execute("INSERT INTO ezproxy_doi VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)", DOI_entry)
		cursor.execute("SELECT last_insert_rowid()")
		item_id = cursor.fetchone()[0]
	elif mode == "mysql":
		DOI_entry = (title, DOI, DOI_link)
		cursor.execute('''INSERT INTO ezproxy_doi_items
			(id, title, doi, doi_link) VALUES (NULL, %s, %s, %s)
		''', DOI_entry)
		cursor.execute("SELECT LAST_INSERT_ID()")
		item_id = cursor.fetchone()[0]

	print(f"Item {DOI} inserted.")
	return item_id

def add_all_items_to_db(web_resources, mysql_cursor, sqlite_cursor, mysql_conn, sqlite_conn, mode):
	mysql_cursor.execute("SELECT DISTINCT(address) FROM ezproxy_spu_doi")
	data = [item[0] for item in mysql_cursor.fetchall()]

	mysql_cursor.execute("SELECT DISTINCT(address) FROM ezproxy_spu_doi WHERE ezproxy_doi_id IS NOT NULL")
	subtract = [item[0] for item in mysql_cursor.fetchall()]

	data = [item for item in data if item not in subtract]

	# unique = []
	# for item in data:
	# 	unique.append(item[0])
	# data = list(set(unique))

	DOI_links = get_DOI_links(data, web_resources)

	index = 1
	for address in DOI_links:
		DOI_link = DOI_links[address]
		if DOI_link:
			if mode == "sqlite":
				item_id = insert_entry(DOI_link, sqlite_cursor, "sqlite")
			elif mode == "mysql":
				item_id = insert_entry(DOI_link, mysql_cursor, "mysql")
				if item_id:
					mysql_cursor.execute("UPDATE ezproxy_spu_doi SET ezproxy_doi_id = %s WHERE address = %s", (item_id, address))
				mysql_conn.commit()
			print(f"Link {index} of {len(DOI_links.values())} processed.")
		else:
			print(f"Link {index} of {len(DOI_links.values())} is blank, skipping.")
		index += 1
	return DOI_links

# Build database routine
def doi_db_routine(mode = "sqlite"):
	ezproxy_conn = connect_to_ezproxy_db()
	ezproxy_cursor = ezproxy_conn.cursor()
	if mode == "sqlite":
		sqlite_conn = connect_to_output_db()
		sqlite_cursor = sqlite_conn.cursor()
		setup_output_db(sqlite_cursor)
		DOI_links = add_all_items_to_db(web_resources, ezproxy_cursor, sqlite_cursor, mode)
	elif mode == "mysql":
		setup_ezproxy_items_table(ezproxy_cursor)
		DOI_links = add_all_items_to_db(web_resources, ezproxy_cursor, None, ezproxy_conn, None, mode)

	print("Saving database...")
	ezproxy_conn.commit()
	ezproxy_conn.close()
	print("Saved.")
		
doi_db_routine("mysql")