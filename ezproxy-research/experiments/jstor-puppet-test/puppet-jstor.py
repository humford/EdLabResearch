import sys
import re
import mysql.connector
from Naked.toolshed.shell import execute_js, muterun_js
from bs4 import BeautifulSoup

def get_ezproxy_db():
	researchdb = mysql.connector.connect (
		host = "analytics.tc-library.org",
		user = "research",
		passwd = "S@YZfH",
		database = "ezproxy-logs-oclc"
	)
	return researchdb

def get_DOI_JSTOR(JSTOR_link):
	response = muterun_js("puppet-jstor.js", JSTOR_link)

	if response.exitcode == 0:
		soup= BeautifulSoup(response.stdout, "html.parser")
		print(soup.prettify())
		doi_div = soup.find("div", class_="doi")
		possible = re.search(r"DOI: (.*)", doi_div.text)
		if possible:
			return possible.group(1)
		else:
			return None
	else:
		#Want to actually retry
		return None
		#sys.stderr.write(response.stderr)

def get_JSTOR_links(mysql_cursor):
	mysql_cursor.execute("SELECT address FROM ezporxy_spu WHERE web = \"www.jstor.org\"")
	links = [item[0] for item in mysql_cursor.fetchall()]
	return links

#ezproxy = get_ezproxy_db()
#mysql_cursor = ezproxy.cursor()

print(get_DOI_JSTOR(input("JSTOR URL: ")))