import mysql.connector
from urllib.parse import urlparse
from urllib.parse import parse_qsl
from urllib.parse import urlencode
import requests 
from xml.etree import ElementTree
import xmltodict
import json
import sys
import re
import sqlite3
from collections import OrderedDict
from Naked.toolshed.shell import execute_js, muterun_js
from bs4 import BeautifulSoup

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

def trim_netloc(netloc):
	regex = r"www\.(.*)"
	if re.match(regex, netloc):
		trimmed = re.search(regex, netloc).group(1)
		return trimmed
	else:
		return netloc

def prep_data(data):
	prepped = []
	for item in data:
		prepped.append(item[0])
	prepped = list(set(prepped))
	return prepped

def DOI_from_OpenURL(query):
	regex = r"doi:([^&]*)"
	DOI = None
	params = parse_qsl(query)
	for param in params:
		if param[0] == "id":
			possible = re.search(doi_regex, param[1])
			if possible:
				DOI = possible.group(1)
				break
	return DOI

def trim_params(query):
	params = parse_qsl(query)
	for param in params:
		if param[0] in ["rft_val_fmt"]:
			params.remove(param)
	return urlencode(params)

def make_DOI_query(link):
	DOI_base_URL = "https://doi.crossref.org/openurl?pid=htw2116@columbia.edu"
	parsed_link = urlparse(URL)
	return DOI_base_URL + "&redirect=false&" + trim_params(parsed_link.query)

def DOI_from_link(DOI_link):
	if DOI_link:
		try:
			xmldict = xmltodict.parse(requests.get(DOI_link).content)
		except:
			#print(requests.get(DOI_link).content)
			return None
		if xmldict:
			#print(json.dumps(xmldict, indent=4))
			if "crossref_result" in xmldict:
				if "query_result" in xmldict["crossref_result"]:
					if "body" in xmldict["crossref_result"]["query_result"]:
						if "query" in xmldict["crossref_result"]["query_result"]["body"]:
							if "doi" in xmldict["crossref_result"]["query_result"]["body"]["query"]:
								if "#text" in xmldict["crossref_result"]["query_result"]["body"]["query"]["doi"]:
									return xmldict["crossref_result"]["query_result"]["body"]["query"]["doi"]["#text"]
								else:
									return None
							else:
								return None
						else:
							return None
					else:
						return None
				else:
					return None
			else:
				return None
		return None
	else:
		return None

def title_from_link(DOI_link):
	if DOI_link:
		try:
			xmldict = xmltodict.parse(requests.get(DOI_link).content)
		except:
			return None
		if xmldict:
			if "crossref_result" in xmldict:
				if "query_result" in xmldict["crossref_result"]:
					if "body" in xmldict["crossref_result"]["query_result"]:
						if "query" in xmldict["crossref_result"]["query_result"]["body"]:
							if "article_title" in xmldict["crossref_result"]["query_result"]["body"]["query"]:
								if "#text" in xmldict["crossref_result"]["query_result"]["body"]["query"]["article_title"]:
									return xmldict["crossref_result"]["query_result"]["body"]["query"]["article_title"] ["#text"] 
								else: 
									return xmldict["crossref_result"]["query_result"]["body"]["query"]["article_title"] 
							else:
								return None
						else:
							return None
					else:
						return None
				else:
					return None
			else:
				return None
		return None
	else:
		return None

#ParseResult(scheme='https', netloc='doi.crossref.org', path='/openurl', params='', query='issn=03603016&volume=54&issue=2&spage=215&date=2002&multihit=true&pid=username:password', fragment='')
#ParseResult(scheme='http', netloc='dx.doi.org', path='/10.1007/s10212-015-0258-5', params='', query='', fragment='')

def compile_params(parsed_link):
	params = parse_qsl(trim_params(parsed_link.query))
	params.append(("pid", "htw2116@columbia.edu"))
	params.append(("redirect", "false"))
	return "https://doi.crossref.org/openurl?" + urlencode(params)

def convert_DOIorg_link(parsed_link):
	doi_regex = r"^/(10.*/.*)$"
	possible = re.search(doi_regex, parsed_link.path)
	if not possible: return None
	DOI = possible.group(1)
	params = [("pid", "htw2116@columbia.edu"), ("redirect", "false"), ("id", f"doi:{DOI}")]
	return "https://doi.crossref.org/openurl?" + urlencode(params)

def convert_openurlEBSCO_link(parsed_link):
	return compile_params(parsed_link)

#gale = "http://find.galegroup.com/openurl/openurl?url_ver=Z39.88-2004&ctx_enc=info:ofi:enc:UTF-8&rft_val_fmt=info:ofi:/fmt:kev:mtx:journal&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&req_dat=info:sid/gale:ugnid:new30429&res_id=info%3Asid%2Fgale%3AHRCA&rft.issn=2320-4664&rft.volume=4&rft.issue=3&rft.spage=315&rft.atitle=Effectiveness+of+visual+auditory+kinaesthetic+tactile+technique+on+reading+level+among+dyslexic+children+at+Helikx+Open+School+and+Learning+Centre%2C+Salem"

def convert_galegroup_link(parsed_link):
	if "openurl" in parsed_link.path:
		return compile_params(parsed_link)
	else:
		return None

def convert_tandforonline_link(parsed_link):
	doi_regex = r"/(10.*/.*)$"
	if "openurl" in parsed_link.path:
		return compile_params(parsed_link)
	elif "doi" in parsed_link.path:
		possible = re.search(doi_regex, parsed_link.path)
		if not possible: return None
		DOI = possible.group(1)
		params = [("pid", "htw2116@columbia.edu"), ("redirect", "false"), ("id", f"doi:{DOI}")]
		return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def convert_psycnet_link(parsed_link):
	if "doi" in parsed_link.path:
		doi_regex = r"/(10.*/.*)$"
		possible = re.search(doi_regex, parsed_link.path)
		if not possible: return None
		DOI = possible.group(1)
		params = [("pid", "htw2116@columbia.edu"), ("redirect", "false"), ("id", f"doi:{DOI}")]
		return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def convert_sagepub_link(parsed_link):
	if "doi" in parsed_link.path:
		doi_regex = r"/(10.*/.*)$"
		possible = re.search(doi_regex, parsed_link.path)
		if not possible: return None
		DOI = possible.group(1)
		params = [("pid", "htw2116@columbia.edu"), ("redirect", "false"), ("id", f"doi:{DOI}")]
		return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def get_DOI_JSTOR(JSTOR_link, attempt = 1):
	response = muterun_js("puppet-jstor.js", JSTOR_link)

	if response.exitcode == 0:
		soup = BeautifulSoup(response.stdout, "html.parser")
		captcha = soup.find(id = "g-recaptcha-response")
		if not captcha:
			doi_div = soup.find("div", class_="doi")
			if doi_div:	
				possible = re.search(r"DOI: (.*)", doi_div.text)
				if possible:
					print("JSTOR DOI Found: " + possible.group(1))
					return possible.group(1)
				else:
					return None
			else:
				return None
		elif attempt < 5:
			print("JSTOR captcha, retrying...")
			return get_DOI_JSTOR(JSTOR_link, attempt + 1)
		else:
			return None
	elif attempt < 5:
		print("No JSTOR response, retrying...")
		return get_DOI_JSTOR(JSTOR_link, attempt + 1)
	else:
		return None

def convert_JSTOR_link(parsed_link):
	if "openurl" in parsed_link.path:
		return compile_params(parsed_link)
	#elif re.search(r"(/stable/\d)", parsed_link.path):
	#	DOI = get_DOI_JSTOR("https://www.jstor.org" + parsed_link.path)
	#	params = [("pid", "htw2116@columbia.edu"), ("redirect", "false"), ("id", f"doi:{DOI}")]
	#	return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def convert_wiley_link(parsed_link):
	if "openurl" in parsed_link.path:
		return compile_params(parsed_link)
	else:
		return None

def convert_springer_link(parsed_link):
	if "openurl" in parsed_link.path:
		return compile_params(parsed_link)
	elif not ("article" in parsed_link.path or "chapter" in parsed_link.path):
		doi_regex = r"^/(10.*/.*)$"
		possible = re.search(doi_regex, parsed_link.path)
		if not possible: return None
		DOI = possible.group(1)
		params = [("pid", "htw2116@columbia.edu"), ("redirect", "false"), ("id", f"doi:{DOI}")]
		return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def convert_emerald_link(parsed_link):
	doi_regex = r"^/(10.*/.*)$"
	possible = re.search(doi_regex, parsed_link.path)
	if not possible: return None
	DOI = possible.group(1)
	params = [("pid", "htw2116@columbia.edu"), ("redirect", "false"), ("id", f"doi:{DOI}")]
	return "https://doi.crossref.org/openurl?" + urlencode(params)

def no_convert(parsed_link):
	return None

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

def convert_user_activity(web_resources, mysql_cursor, sqlite_cursor):
	setup_output_db(sqlite_cursor)
	pass

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
			response = info_from_DOI(DOI)
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
			print(f"Skipped links {ezproxy_doi_id} of {len(data)} - No DOI.")
			continue
		if item[5] or item[6] or item[7]:
			print(f"Skipped links {ezproxy_doi_id} of {len(data)} - Found in cache.")
			continue
		links = get_DOI_links(DOI)
		print(links)
		sqlite_cursor.execute("UPDATE ezproxy_doi SET pdf_link = ? WHERE ezproxy_doi_id = ?", (links["application/pdf"], ezproxy_doi_id))
		sqlite_cursor.execute("UPDATE ezproxy_doi SET xml_link = ? WHERE ezproxy_doi_id = ?", (links["application/xml"], ezproxy_doi_id))
		sqlite_cursor.execute("UPDATE ezproxy_doi SET unspecified_link = ? WHERE ezproxy_doi_id = ?", (links["application/pdf"], ezproxy_doi_id))
		print(f"Added links for {ezproxy_doi_id} of {len(data)}.")
	return

def add_subjects_tables(sqlite_cursor):
	sqlite_cursor.execute("CREATE TABLE IF NOT EXISTS subjects (subject_id INTEGER PRIMARY KEY, subject TEXT)")
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS doi_subjects 
			(ezproxy_doi_id INTEGER, subject_id INTEGER, FOREIGN KEY(ezproxy_doi_id) REFERENCES ezproxy_doi(ezproxy_doi_id), FOREIGN KEY(subject_id) REFERENCES subjects(subject_id))''')
	return

def get_DOI_subjects(DOI):
	subjects = []
	found = False
	while not found:
		try:
			response = info_from_DOI(DOI)
			if response:
				found = True
		except json.decoder.JSONDecodeError:
			if requests.get("https://doi.org/" + DOI, headers = {"Accept":"application/vnd.citationstyles.csl+json"}).content == "Resource not found.":
				continue
			else:
				print("Not found on doi.org")
				return subjects
	if "subject" in response.keys():
		subjects = response["subject"]
	return subjects

def add_subjects(sqlite_cursor, conn):
	sqlite_cursor.execute("SELECT * FROM ezproxy_doi")
	data = sqlite_cursor.fetchall()[::1]

	for item in data:
		ezproxy_doi_id = item[0]
		DOI = item[2]
		if not DOI:
			print(f"Skipped getting subjects {ezproxy_doi_id} of {len(data)} - No DOI.")
			continue
		sqlite_cursor.execute("SELECT * FROM doi_subjects WHERE ezproxy_doi_id = ?", (ezproxy_doi_id, ))
		response = sqlite_cursor.fetchone()
		if response:
			print(f"Skipped getting subjects {ezproxy_doi_id} of {len(data)} - Found in cache.")
			continue
		subjects = get_DOI_subjects(DOI)
		if subjects:
			print(subjects)
			for subject in subjects:
				sqlite_cursor.execute("SELECT subject_id FROM subjects WHERE subject = ?", (subject, ))
				try:
					subject_id = sqlite_cursor.fetchone()[0]
				except TypeError:
					sqlite_cursor.execute("INSERT INTO subjects VALUES (NULL, ?)", (subject, ))
					sqlite_cursor.execute("SELECT last_insert_rowid()")
					subject_id = sqlite_cursor.fetchone()[0]

				sqlite_cursor.execute("INSERT INTO doi_subjects VALUES (?, ?)", (ezproxy_doi_id, subject_id))
		conn.commit()
		print(f"Added subjects for {ezproxy_doi_id} of {len(data)}.")

def add_journals_tables():
	pass

web_resources = {
	"ebookcentral.proquest.com" : no_convert,
	"openurl.ebscohost.com" : convert_openurlEBSCO_link,
	"journals.sagepub.com" : convert_sagepub_link,
	"search.proquest.com" : no_convert,
	"tc.summon.serialssolutions.com" : no_convert,
	"tandfonline.com" : convert_tandforonline_link,
	"link.galegroup.com" : no_convert,
	"jstor.org" : convert_JSTOR_link,
	"go.galegroup.com" : no_convert,
	"find.galegroup.com" : convert_galegroup_link,
	"psycnet.apa.org" : convert_psycnet_link,
	"site.ebrary.com" : no_convert,
	"emeraldinsight.com" : convert_emerald_link,
	"ncte.org" : no_convert,
	"search.epnet.com" : no_convert,
	"link.springer.com" : convert_springer_link,
	"web.b.ebscohost.com" : no_convert,
	"media.proquest.com" : no_convert,
	"web.a.ebscohost.com" : no_convert,
	"vnweb.hwwilsonweb.com" : no_convert,
	"doi.org" : convert_DOIorg_link,
	"dx.doi.org" : convert_DOIorg_link,
	"search.ebscohost.com.eduproxy.tc-library.org:8080" : no_convert,
	"content.apa.org" : no_convert,
	"onlinelibrary.wiley.com" : convert_wiley_link
}

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

ezproxy = get_ezproxy_db()
mysql_cursor = ezproxy.cursor()

#convert_all(web_resources, mysql_cursor, sqlite_cursor)
add_subjects_tables(sqlite_cursor)
add_subjects(sqlite_cursor, conn)

print("Saving database...")
conn.commit()
conn.close()
print("Saved")

#mysql_cursor.execute("SELECT address FROM ezporxy_spu") 
#mysql_cursor.execute("SELECT * FROM ezporxy_spu WHERE web = \"openurl.ebscohost.com\" OR web = \"find.galegroup.com\" OR web = \"doi.org\" OR web = \"dx.doi.org\" OR web = \"www.tandfonline.com\" OR web = \"journals.sagepub.com\" OR \"psycnet.apa.org\"")
#print(len(list(set(mysql_cursor.fetchall()))))

# 92825 unique
# unique = []
# for item in data[::1]:
# 	print(f'{item[0]}')
# 	if "openurl" in item[0]:
# 		unique.append(item[0])
# data = list(set(unique))

# print(len([d for d in data if "openurl" in d])) 

# DOIs = get_DOIs(data[::1], web_resources)

# real_DOIs = [DOIs[DOI] for DOI in DOIs if DOIs[DOI]]

# print(len(real_DOIs))


