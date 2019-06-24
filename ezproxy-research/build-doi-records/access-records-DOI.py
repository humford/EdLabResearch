import mysql.connector
import sqlite3
from urllib.parse import urlparse
from urllib.parse import parse_qsl
from urllib.parse import urlencode
import requests 
from xml.etree import ElementTree
import xmltodict
import re

# OLD
def trim_params(query):
	params = parse_qsl(query)
	for param in params:
		if param[0] in ["rft_val_fmt"]:
			params.remove(param)
	return urlencode(params)

def trim_netloc(netloc):
	regex = r"www\.(.*)"
	if re.match(regex, netloc):
		trimmed = re.search(regex, netloc).group(1)
		return trimmed
	else:
		return netloc

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






# SETUP
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
		(ezproxy_user_id INTEGER PRIMARY KEY, uni TEXT)''')
	sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS access_records
		(access_record_id INTEGER PRIMARY KEY, ezproxy_user_id INTEGER, ezproxy_doi_id INTEGER, session TEXT, datetime TEXT, FOREIGN KEY(ezproxy_user_id) REFERENCES ezproxy_users(ezproxy_user_id), FOREIGN KEY(ezproxy_doi_id) REFERENCES ezproxy_doi(ezproxy_doi_id))''')
	return

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

def get_access_records(mysql_cursor):
	mysql_cursor.execute("SELECT * FROM ezporxy_spu WHERE datetime > %s", ("2019-06-01",))
	spu = mysql_cursor.fetchall()
	mysql_cursor.execute("SELECT * FROM ezproxy_dailylog WHERE datetime > %s", ("2019-06-01",))
	dailylog = mysql_cursor.fetchall()

	return spu, dailylog

def process_user(user, sqlite_cursor):
	if not user:
		print(f"Skipped processing user - Empty.")
	else:
		sqlite_cursor.execute("SELECT ezproxy_user_id FROM ezproxy_users WHERE uni = ?", (user,))
		try:
			ezproxy_user_id = sqlite_cursor.fetchone()[0]
		except TypeError:
			sqlite_cursor.execute("INSERT INTO ezproxy_users VALUES (NULL, ?)", (user,))
			sqlite_cursor.execute("SELECT last_insert_rowid()")
			ezproxy_user_id = sqlite_cursor.fetchone()[0]
	print(f"Processed user {user}.")
	return ezproxy_user_id

def insert_access_records(mysql_cursor, sqlite_cursor):
	global web_resources
	spu, dailylog = get_access_records(mysql_cursor)

	mysql_cursor.execute("SELECT address FROM ezporxy_spu WHERE datetime > %s", ("2019-06-01",))
	data = mysql_cursor.fetchall()
	DOI_links = get_DOI_links(data, web_resources)

	counter = 1
	for record in spu:
		try:
			address = record[5]
		except IndexError:
			continue
			counter += 1
		session = record[3]
		datetime = record[1]
		mysql_cursor.execute("SELECT user FROM ezproxy_dailylog WHERE session = %s", (session,))
		results = mysql_cursor.fetchall()
		if results:
			user = results[0][0]
		else:
			continue
			counter += 1
		ezproxy_user_id = process_user(user, sqlite_cursor)
		DOI = DOI_from_link(DOI_links[address])
		print(DOI)

		sqlite_cursor.execute("SELECT ezproxy_doi_id FROM ezproxy_doi WHERE doi = ?", (DOI,))
		results = sqlite_cursor.fetchall()
		if results:
			ezproxy_doi_id = results[0][0]
		else:
			continue
			counter += 1

		sqlite_cursor.execute("INSERT INTO access_records VALUES (NULL, ?, ?, ?, ?)", (ezproxy_user_id, ezproxy_doi_id, session, datetime))
		print(f"Processed item {ezproxy_doi_id}. ({counter} of {len(data)})")
		counter += 1


sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("../ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

ezproxy = get_ezproxy_db()
mysql_cursor = ezproxy.cursor()

add_records_tables(sqlite_cursor)
insert_access_records(mysql_cursor, sqlite_cursor)

print("Saving database...")
conn.commit()
conn.close()
print("Saved")


