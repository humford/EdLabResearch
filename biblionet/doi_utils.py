# Import Configuration
from .config import config

crossref_email = config["API"]["CROSSREF_EMAIL"]

# Import Internal
from .db_utils import *

# Import External
import re
import xmltodict
from urllib.parse import urlparse, parse_qsl, urlencode

# MAIN

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