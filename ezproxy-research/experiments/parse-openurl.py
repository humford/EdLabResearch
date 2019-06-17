from urllib.parse import urlparse
from urllib.parse import parse_qsl
from urllib.parse import urlencode
import re
import requests 
from xml.etree import ElementTree
import xmltodict
import json

link = "http://find.galegroup.com/openurl/openurl?url_ver=Z39.88-2004&ctx_enc=info:ofi:enc:UTF-8&rft_val_fmt=info:ofi:/fmt:kev:mtx:journal&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&req_dat=info:sid/gale:ugnid:new30429&res_id=info%3Asid%2Fgale%3APPDS&rft.issn=0888-6601&rft.volume=9&rft.issue=4&rft.spage=341&rft.atitle=%22Start+the+Revolution%22%3A+Hip+Hop+Music+and+Social+Justice+Education"

wiley = "http://onlinelibrary.wiley.com/resolve/openurl?genre=article&eissn=1467-9922&volume=60&issue=1&spage=221"

ebscohost = "http://openurl.ebscohost.com/linksvc/linking.aspx?genre=article&issn=0001-6993&title=Acta+sociologica&date=1996&volume=39&issue=1&spage=116&atitle=Sociological+Theory%3A+What+Went+Wrong+Diagnosis+and+Remedies&aulast=Swedberg&aufirst=Richard"

ajp = "https://ajp.psychiatryonline.org/openurl?url_ver=Z39.88-2004&rft.genre=article&rft.issn=0002-953X&rft.volume=167&issue=6&rft.spage=726&atitle=Xenophobia%2C+Immigration%2C+and+Mental+Health"

gale = "http://find.galegroup.com/openurl/openurl?url_ver=Z39.88-2004&ctx_enc=info:ofi:enc:UTF-8&rft_val_fmt=info:ofi:/fmt:kev:mtx:journal&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&req_dat=info:sid/gale:ugnid:new30429&res_id=info%3Asid%2Fgale%3AHRCA&rft.issn=2320-4664&rft.volume=4&rft.issue=3&rft.spage=315&rft.atitle=Effectiveness+of+visual+auditory+kinaesthetic+tactile+technique+on+reading+level+among+dyslexic+children+at+Helikx+Open+School+and+Learning+Centre%2C+Salem"

gateway = "http://gateway.proquest.com/openurl?ctx_ver=Z39.88-2004&res_dat=xri:pqm&rft_val_fmt=ori/fmt:kev:mtx:journal&rfr_id=info:xri/sid:summon&genre=article&issn=0024-9033&jtitle=McGill+journal+of+education&volume=51&issue=3&spage=1223&atitle=Linda+Darling-Hammond+%26+Robert+Rothman+Teaching+in+the+Flat+World&req_dat=xri:pqm:accountid=14258"
# res_dat, rft_dat

sagepub = "http://journals.sagepub.com/openurl?url_ver=Z39.88-2004&rft.genre=article&rft.issn=1476-718X&rft.date=2016&rft.volume=14&rft.issue=2&rft.spage=146&rft.atitle=Associations+among+Preschool+Children%27s+Classroom+Literacy+Environment%2C+Interest+and+Engagement+in+Literacy+Activities%2C+and+Early+Reading+Skills&utm_source=360link&utm_medium=discovery-provider"

springer = "https://link.springer.com/openurl.asp?genre=article&id=doi:10.1007/s10608-016-9762-4"

emerald = "https://www.emeraldinsight.com/openurl?genre=article&issn=0143-7720&date=2010&volume=31&issue=4&spage=426"

links = [wiley, ebscohost, ajp, gale, gateway, sagepub, springer, emerald]

def title_from_link(DOI_link):
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
							if "article_title" in xmldict["crossref_result"]["query_result"]["body"]["query"]:
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

def find_DOI(query):
	regex = r"doi:([^&]*)"
	DOI = None
	params = parse_qsl(query)
	for param in params:
		if param[0] == "id":
			possible = re.sub(regex, "\\1", param[1])
			if possible:
				DOI = possible
				break
	return DOI

def trim_params(query):
	params = parse_qsl(query)
	for param in params:
		if param[0] in ["rft_val_fmt"]:
			params.remove(param)
	return urlencode(params)

def make_DOI_query(URL):
	DOI_base_URL = "https://doi.crossref.org/openurl?pid=htw2116@columbia.edu"
	parsed_link = urlparse(URL)
	return DOI_base_URL + "&redirect=false&" + trim_params(parsed_link.query)

def get_DOI(URL):
	xmldict = xmltodict.parse(requests.get(URL).content)
	return xmldict["crossref_result"]["query_result"]["body"]["query"]["doi"]["#text"]

URL_to_parse = input("URL To Parse: ")

print(title_from_link(make_DOI_query(URL_to_parse)))

# query = urlparse(URL_to_parse).query

# for link in links:
# 	print(make_DOI_query(link))

# print(find_DOI(springer))