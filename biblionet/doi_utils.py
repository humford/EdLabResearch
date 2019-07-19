# Import Configuration
from config import config

crossref_email = config["API"]["CROSSREF_EMAIL"]

# Import Internal
from db_utils import *

# Import External
import re
import requests
from habanero import Crossref
import xmltodict
from urllib.parse import urlparse, parse_qsl, urlencode

# MAIN

# Get general metadata from a DOI
def info_from_DOI(DOI):
	cr = Crossref(mailto = crossref_email)
	return cr.works(ids = DOI)
	#return requests.get("https://doi.org/" + DOI, headers = {"Accept":"application/vnd.citationstyles.csl+json"}).json()

# Get links to PDFs and other items from a DOI
def get_DOI_item_links(DOI):
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

# Trim netloc from url
def trim_netloc(netloc):
	regex = r"www\.(.*)"
	if re.match(regex, netloc):
		trimmed = re.search(regex, netloc).group(1)
		return trimmed
	else:
		return netloc

# Trim invalid params
def trim_params(query):
	params = parse_qsl(query)
	for param in params:
		if param[0] in ["rft_val_fmt"]:
			params.remove(param)
	return urlencode(params)

# Compile params into valid request to the Crossref OpenURL API
def compile_params(parsed_link):
	global crossref_email
	params = parse_qsl(trim_params(parsed_link.query))
	params.append(("pid", crossref_email))
	params.append(("redirect", "false"))
	return "https://doi.crossref.org/openurl?" + urlencode(params)

# Get DOI if it is in the OpenURL query
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

# Get DOI from a properly formatted request to the Crossref OpenURL API
def DOI_from_link(DOI_link):
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

# Get title from a properly formatted request to the Crossref OpenURL API
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

# Title from DOI
def title_from_DOI(DOI):
	cr = Crossref(mailto = crossref_email)
	response = cr.works(ids = DOI)
	if "message" in response:
		if "title" in response["message"]:
			if response["message"]["title"]:
				return response["message"]["title"][0]
	return None

# CONVERSION FUNCTIONS

def convert_DOIorg_link(parsed_link):
	doi_regex = r"^/(10.*/.*)$"
	possible = re.search(doi_regex, parsed_link.path)
	if not possible: return None
	DOI = possible.group(1)
	params = [("pid", crossref_email), ("redirect", "false"), ("id", f"doi:{DOI}")]
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
		params = [("pid", crossref_email), ("redirect", "false"), ("id", f"doi:{DOI}")]
		return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def convert_psycnet_link(parsed_link):
	if "doi" in parsed_link.path:
		doi_regex = r"/(10.*/.*)$"
		possible = re.search(doi_regex, parsed_link.path)
		if not possible: return None
		DOI = possible.group(1)
		params = [("pid", crossref_email), ("redirect", "false"), ("id", f"doi:{DOI}")]
		return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def convert_sagepub_link(parsed_link):
	if "doi" in parsed_link.path:
		doi_regex = r"/(10.*/.*)$"
		possible = re.search(doi_regex, parsed_link.path)
		if not possible: return None
		DOI = possible.group(1)
		params = [("pid", crossref_email), ("redirect", "false"), ("id", f"doi:{DOI}")]
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
	#	params = [("pid", crossref_email), ("redirect", "false"), ("id", f"doi:{DOI}")]
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
		params = [("pid", crossref_email), ("redirect", "false"), ("id", f"doi:{DOI}")]
		return "https://doi.crossref.org/openurl?" + urlencode(params)
	else:
		return None

def convert_emerald_link(parsed_link):
	doi_regex = r"^/(10.*/.*)$"
	possible = re.search(doi_regex, parsed_link.path)
	if not possible: return None
	DOI = possible.group(1)
	params = [("pid", crossref_email), ("redirect", "false"), ("id", f"doi:{DOI}")]
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