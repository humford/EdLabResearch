# Get DOIs from ezproxy
import sqlite3

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("../ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

sqlite_cursor.execute("SELECT doi FROM ezproxy_doi WHERE doi IS NOT NULL")
DOIs = [item[0] for item in sqlite_cursor.fetchall()]

# Build a Graph Tools Representation of DOI Metadata Structure
# Need a list of valid DOIs

from halo import Halo
from graph_tool.all import *
from habanero import Crossref
from requests.exceptions import HTTPError, ConnectionError
from pprint import pprint
from time import sleep

# AUTHOR ROUTINE
def create_author_graph(directed = True):
	graph = Graph(directed = directed)
	# ID
	# types: DOI, ISSN, ASJC code, ORCID
	item_id = graph.new_vertex_property("string")
	graph.vp.id = item_id

	# Name
	# types: paper title, journal name, subject name, author name
	item_name = graph.new_vertex_property("string")
	graph.vp.name = item_name

	# Type
	# types: author (3), paper (2), journal (1), subject (0)
	item_type = graph.new_vertex_property("int")
	graph.vp.type = item_type

	# Author Type
	# types: first (1), additional (0)
	item_author_type = graph.new_edge_property("int")
	graph.ep.author_type = item_author_type

	# Author Info
	# types: dictionary of author info from API
	item_author_info = graph.new_vertex_property("object")
	graph.vp.author_info = item_author_info

	return graph

def process_authors(graph, authors):
	global vertex_dict

	author_vertices = []

	for author in authors:
		if "given" in author and "family" in author:
			author_name = author["given"] + " " + author["family"]
		elif "given" in author:
			author_name = author["given"] 
		elif "family" in author:
			author_name = author["family"]
		else:
			continue

		if author_name in vertex_dict["author"]:
			author_index = vertex_dict["author"][author_name]
			author_vertex = graph.vertex(author_index)
			author_vertices.append(author_index)

			message = "Author " + author_name + " found in network."
			update_progress(message, "found")
		else:
			author_vertex = graph.add_vertex()
			if "ORCID" in author:
				graph.vp.id[author_vertex] = author["ORCID"]
			graph.vp.name[author_vertex] = author_name
			graph.vp.type[author_vertex] = 3
			graph.vp.author_info[author_vertex] = author

			vertex_dict["author"][author_name] = int(author_vertex)
			author_vertices.append(author_vertex)

			message = "Author " + author_name + " inserted into network."
			update_progress(message, "inserted")
	return author_vertices

def process_author_paper(graph, DOI, cr):
	global vertex_dict
	global total
	global counter

	try:
		item = cr.works(ids = DOI)
	except HTTPError:
		message = f"HTTPError ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	except TimeoutError:
		message = f"TimeoutError ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return

	if not item["message"]["title"]:
		message = f"Paper {DOI} no title found ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	title = item["message"]["title"][0]

	if not "author" in item["message"]:
		message = f"Paper {DOI} no authors found ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	elif not item["message"]["author"]:
		message = f"Paper {DOI} no authors found ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	authors = item["message"]["author"]

	if DOI in vertex_dict["paper"]:
		message = f"Paper {DOI} found in network. ({counter} of {total})"
		update_progress(message, "found")
		counter += 1
	else:
		author_vertices = process_authors(graph, authors)

		paper_vertex = graph.add_vertex()
		graph.vp.id[paper_vertex] = DOI
		graph.vp.name[paper_vertex] = title
		graph.vp.type[paper_vertex] = 2

		for author_vertex in author_vertices:
			author_edge = graph.add_edge(author_vertex, paper_vertex)
			author = graph.vp.author_info[author_vertex]
			if author["sequence"] == "first":
				graph.ep.author_type[author_edge] = 1
			else:
				graph.ep.author_type[author_edge] = 0

		vertex_dict["paper"][DOI] = int(paper_vertex)
		message = f"Paper {DOI} inserted into network. ({counter} of {total})"
		update_progress(message, "inserted")
		counter += 1

def build_author_graph(graph, DOIs):
	global vertex_dict
	global spinner

	spinner.start()

	cr = Crossref(mailto = "htw2116@columbia.edu")

	for DOI in DOIs:
		process_author_paper(graph, DOI, cr)

	spinner.succeed("Author network built.")

# CITATION ROUTINE
def create_citation_graph(directed = True):
	graph = Graph(directed = directed)
	# ID
	# types: DOI, ISSN, ASJC code
	item_id = graph.new_vertex_property("string")
	graph.vp.id = item_id

	# Name
	# types: paper title, journal name, subject name
	item_name = graph.new_vertex_property("string")
	graph.vp.name = item_name

	# Type
	# types: paper (2), journal (1), subject (0)
	item_type = graph.new_vertex_property("int")
	graph.vp.type = item_type

	return graph

def add_paper(graph, DOI, cr):
	global vertex_dict
	global counter
	global total

	try:
		item = cr.works(ids = DOI)
	except HTTPError:
		message = f"HTTPError. ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return

	if not item["message"]["title"]:
		message = f"Paper {DOI} no title found. ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return

	# Don't add papers without references
	if "reference" in item["message"]:
		if not item["message"]["reference"]:
			message = f"No references for {DOI}. ({counter} of {total})"
			update_progress(message, "fail")
			counter += 1
			return
	else:
		message = f"No references for {DOI}. ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return

	title = item["message"]["title"][0]

	if DOI in vertex_dict["paper"]:
		message = f"Paper {DOI} found in network. ({counter} of {total})"
		update_progress(message, "found")
		counter += 1
	else:
		try:
			paper_vertex = graph.add_vertex()
			
			graph.vp.id[paper_vertex] = DOI
			graph.vp.name[paper_vertex] = title
			graph.vp.type[paper_vertex] = 2

			vertex_dict["paper"][DOI] = int(paper_vertex)
			
			message = f"Paper {DOI} inserted into network. ({counter} of {total})"
			update_progress(message, "inserted")
			counter += 1
		except HTTPError:
			message = f"HTTPError ({counter} of {total})"
			update_progress(message, "fail")
			counter += 1
	return

def process_citations(graph, DOI, cr):
	global vertex_dict

	try:
		item = cr.works(ids = DOI)
	except HTTPError:
		print("HTTPError")
		return

	if "reference" in item["message"]:
		if not item["message"]["reference"]:
			print(f"No references for {DOI}")
			return
	else:
		print(f"No references for {DOI}")
		return

	cited_by_vertex = graph.vertex(vertex_dict["paper"][DOI])

	for reference in item["message"]["reference"]:
		if "DOI" in reference:
			if reference["DOI"] in vertex_dict["paper"]:
				cited_vertex = graph.vertex(vertex_dict["paper"][reference["DOI"]])
				graph.add_edge(cited_vertex, cited_by_vertex)
		else:
			continue

def build_citation_graph(graph, DOIs):
	global vertex_dict
	global spinner

	spinner.start()

	cr = Crossref(mailto = "htw2116@columbia.edu")

	for DOI in DOIs:
		add_paper(graph, DOI, cr)

	spinner.succeed("All papers inserted")
	spinner.start("Building citation edges...")

	for DOI in vertex_dict["paper"]:
		process_citations(graph, DOI, cr)

	spinner.stop()

def create_network_graph():
	graph = Graph()
	# ID
	# types: DOI, ISSN, ASJC code
	item_id = graph.new_vertex_property("string")
	graph.vp.id = item_id

	# Name
	# types: paper title, journal name, subject name
	item_name = graph.new_vertex_property("string")
	graph.vp.name = item_name

	# Type
	# types: paper (2), journal (1), subject (0)
	item_type = graph.new_vertex_property("int")
	graph.vp.type = item_type

	return graph

def update_progress(message, status):
	global spinner

	if status == "inserted":
		spinner.succeed(message)
	elif status == "found":
		spinner.info(message)
	elif status == "fail":
		spinner.fail(message)
	spinner.start("Building network...")

# NETWORK ROUTINE
def process_subjects(graph, subjects):
	global vertex_dict

	subject_vertices = []

	for subject in subjects:
		if subject["ASJC"] in vertex_dict["subject"]:
			subject_index = vertex_dict["subject"][subject["ASJC"]]
			subject_vertex = graph.vertex(subject_index)
			subject_vertices.append(subject_vertex)

			message = "Subject " + str(subject["ASJC"]) + " found in network."
			update_progress(message, "found")
		else:
			subject_vertex = graph.add_vertex()
			graph.vp.id[subject_vertex] = subject["ASJC"]
			graph.vp.name[subject_vertex] = subject["name"]
			#graph.vp.type[subject_vertex] = "subject"
			graph.vp.type[subject_vertex] = 0

			vertex_dict["subject"][subject["ASJC"]] = int(subject_vertex)
			subject_vertices.append(subject_vertex)

			message = "Subject " + str(subject["ASJC"]) + " inserted into network."
			update_progress(message, "inserted")
	return subject_vertices

def process_journal(graph, journal):
	global vertex_dict

	subjects = journal["subjects"]
	subject_vertices = process_subjects(graph, subjects)
	ISSN = journal["ISSN"][0]

	if ISSN in vertex_dict["journal"]:
		journal_index = vertex_dict["journal"][ISSN]
		journal_vertex = graph.vertex(journal_index)

		message = "Journal " + ISSN + " found in network."
		update_progress(message, "found")
	else:
		journal_vertex = graph.add_vertex()
		graph.vp.id[journal_vertex] = ISSN
		if type(journal["title"]) == type(list()):
			title = journal["title"][0]
		else:
			title = journal["title"]
		graph.vp.name[journal_vertex] = title
		#graph.vp.type[journal_vertex] = "journal"
		graph.vp.type[journal_vertex] = 1

		for subject_vertex in subject_vertices:
			graph.add_edge(journal_vertex, subject_vertex)

		vertex_dict["journal"][ISSN] = int(journal_vertex)

		message = "Journal " + ISSN + " inserted into network."
		update_progress(message, "inserted")
	return journal_vertex

def process_paper(graph, DOI, cr):
	global vertex_dict
	global total
	global counter

	try:
		item = cr.works(ids = DOI)
	except HTTPError:
		message = f"HTTPError ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	except TimeoutError:
		message = f"TimeoutError ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return

	if not item["message"]["title"]:
		message = f"Paper {DOI} no title found ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	title = item["message"]["title"][0]

	if DOI in vertex_dict["paper"]:
		message = f"Paper {DOI} found in network. ({counter} of {total})"
		update_progress(message, "found")
		counter += 1
	else:
		try:
			if not "ISSN" in item["message"]:
				return
			
			try:
				journal = cr.journals(ids = item["message"]["ISSN"])
			except HTTPError:
				sleep(5)
				message = f"HTTPError ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return
			except ConnectionError:
				sleep(5)
				message = f"ConnectionError ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return
			except TimeoutError:
				sleep(5)
				message = f"TimeoutError ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return

			if "message" in journal:
				journal = journal["message"]
			elif type(journal) == type(list()):
				journal = journal[0]["message"]
			else:
				message = f"No journal found for paper {DOI}. ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return
			
			journal_vertex = process_journal(graph, journal)

			paper_vertex = graph.add_vertex()
			graph.vp.id[paper_vertex] = DOI
			graph.vp.name[paper_vertex] = title
			#graph.vp.type[paper_vertex] = "paper"
			graph.vp.type[paper_vertex] = 2

			graph.add_edge(paper_vertex, journal_vertex)

			vertex_dict["paper"][DOI] = int(paper_vertex)
			message = f"Paper {DOI} inserted into network. ({counter} of {total})"
			update_progress(message, "inserted")
			counter += 1
		except HTTPError:
			message = f"HTTPError ({counter} of {total})"
			update_progress(message, "fail")
			counter += 1
	return

def build_network_graph(graph, DOIs):
	global spinner
	
	spinner.start()
	cr = Crossref(mailto = "htw2116@columbia.edu")

	for DOI in DOIs:
		process_paper(graph, DOI, cr)
	spinner.stop()

	print("Network built.")

# USER ROUTINE
def create_user_graph(directed = True):
	graph = Graph(directed = directed)
	# ID
	# types: DOI, ISSN, ASJC code, ORCID, UNI
	item_id = graph.new_vertex_property("string")
	graph.vp.id = item_id

	# Name
	# types: paper title, journal name, subject name, author name, user name
	item_name = graph.new_vertex_property("string")
	graph.vp.name = item_name

	# Type
	# types: user (4), author (3), paper (2), journal (1), subject (0)
	item_type = graph.new_vertex_property("int")
	graph.vp.type = item_type

	# Times Accessed
	# types: count accessed
	item_times_accessed = graph.new_edge_property("int")
	graph.ep.times_accessed = item_times_accessed

	# Vertex Dict
	# For finding vertices by id
	item_vertex_dict = graph.new_graph_property("object")
	graph.gp.vertex_dict = item_vertex_dict

	return graph

def user_process_paper(graph, DOI, cr):
	global vertex_dict

	try:
		item = cr.works(ids = DOI)
	except HTTPError:
		message = f"HTTPError"
		update_progress(message, "fail")
		return None
	except TimeoutError:
		message = f"TimeoutError"
		update_progress(message, "fail")
		return None

	if not item["message"]["title"]:
		message = f"Paper {DOI} no title found"
		update_progress(message, "fail")
		return None
	title = item["message"]["title"][0]

	if DOI in vertex_dict["paper"]:
		message = f"Paper {DOI} found in network."
		update_progress(message, "found")
		paper_index = vertex_dict["paper"][DOI]
		paper_vertex = graph.vertex(paper_index)
	else:
		try:
			paper_vertex = graph.add_vertex()
			graph.vp.id[paper_vertex] = DOI
			graph.vp.name[paper_vertex] = title
			graph.vp.type[paper_vertex] = 2

			vertex_dict["paper"][DOI] = int(paper_vertex)
			message = f"Paper {DOI} inserted into network."
			update_progress(message, "inserted")
		except HTTPError:
			message = f"HTTPError"
			update_progress(message, "fail")
	return paper_vertex

def process_user(graph, uni, cr):
	global vertex_dict
	global total
	global counter
	global sqlite_cursor

	sqlite_cursor.execute("SELECT ezproxy_user_id FROM ezproxy_users WHERE uni = ?", (uni,))
	user_id = sqlite_cursor.fetchone()[0]

	sqlite_cursor.execute("SELECT ezproxy_doi_id FROM access_records WHERE ezproxy_doi_id = ?", (user_id,))
	records = [item[0] for item in sqlite_cursor.fetchall()]

	if uni in vertex_dict["user"]:
		message = f"User {uni} found in network. ({counter} of {total})"
		user_vertex = vertex_dict["user"][uni]
		user_vertex = graph.vertex(user_index)
		update_progress(message, "found")
		counter += 1
	else:
		user_vertex = graph.add_vertex()
		graph.vp.id[user_vertex] = uni
		graph.vp.name[user_vertex] = user_id
		graph.vp.type[user_vertex] = 4

		vertex_dict["user"][uni] = int(user_vertex)
		message = f"User {uni} inserted into network. ({counter} of {total})"
		update_progress(message, "inserted")
		counter += 1

	for record in records:
		sqlite_cursor.execute("SELECT doi FROM ezproxy_doi WHERE ezproxy_doi_id = ?", (record,))
		try:
			DOI = sqlite_cursor.fetchone()[0]
		except TypeError:
			continue

		paper_vertex = user_process_paper(graph, DOI, cr)
		if paper_vertex:
			prior_access_edge = graph.edge(user_vertex, paper_vertex)
			if prior_access_edge:
				graph.ep.times_accessed[prior_access_edge] += 1
			else:
				access_edge = graph.add_edge(user_vertex, paper_vertex)
				graph.ep.times_accessed[access_edge] = 1

	return

def build_user_graph(graph, users):
	global vertex_dict
	global spinner

	spinner.start()
	cr = Crossref(mailto = "hwill12345@gmail.com")

	for uni in users:
		process_user(graph, uni, cr)

	spinner.succeed("All users inserted")

	spinner.stop()

# COMBINED ROUTINE	 
def create_combined_graph(directed = True):
	graph = Graph(directed = directed)
	# ID
	# types: DOI, ISSN, ASJC code, ORCID
	item_id = graph.new_vertex_property("string")
	graph.vp.id = item_id

	# Name
	# types: paper title, journal name, subject name, author name
	item_name = graph.new_vertex_property("string")
	graph.vp.name = item_name

	# Type
	# types: author (3), paper (2), journal (1), subject (0)
	item_type = graph.new_vertex_property("int")
	graph.vp.type = item_type

	# Author Type
	# types: first (1), additional (0)
	item_author_type = graph.new_edge_property("int")
	graph.ep.author_type = item_author_type

	# Author Info
	# types: dictionary of author info from API
	item_author_info = graph.new_vertex_property("object")
	graph.vp.author_info = item_author_info

	return graph

def combined_process_paper(graph, DOI, cr):
	global vertex_dict
	global total
	global counter

	try:
		item = cr.works(ids = DOI)
	except HTTPError:
		message = f"HTTPError ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	except TimeoutError:
		message = f"TimeoutError ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return

	if not item["message"]["title"]:
		message = f"Paper {DOI} no title found ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	title = item["message"]["title"][0]

	if not "author" in item["message"]:
		message = f"Paper {DOI} no authors found ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	elif not item["message"]["author"]:
		message = f"Paper {DOI} no authors found ({counter} of {total})"
		update_progress(message, "fail")
		counter += 1
		return
	authors = item["message"]["author"]

	if DOI in vertex_dict["paper"]:
		message = f"Paper {DOI} found in network. ({counter} of {total})"
		update_progress(message, "found")
		counter += 1
	else:
		try:
			if not "ISSN" in item["message"]:
				return

			try:
				journal = cr.journals(ids = item["message"]["ISSN"])
			except HTTPError:
				sleep(5)
				message = f"HTTPError ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return
			except ConnectionError:
				sleep(5)
				message = f"ConnectionError ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return
			except TimeoutError:
				sleep(5)
				message = f"TimeoutError ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return

			if "message" in journal:
				journal = journal["message"]
			elif type(journal) == type(list()):
				journal = journal[0]["message"]
			else:
				message = f"No journal found for paper {DOI}. ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return
			
			journal_vertex = process_journal(graph, journal)
			author_vertices = process_authors(graph, authors)

			paper_vertex = graph.add_vertex()
			graph.vp.id[paper_vertex] = DOI
			graph.vp.name[paper_vertex] = title
			graph.vp.type[paper_vertex] = 2

			graph.add_edge(paper_vertex, journal_vertex)

			for author_vertex in author_vertices:
				author_edge = graph.add_edge(author_vertex, paper_vertex)
				author = graph.vp.author_info[author_vertex]
				if author["sequence"] == "first":
					graph.ep.author_type[author_edge] = 1
				else:
					graph.ep.author_type[author_edge] = 0

			vertex_dict["paper"][DOI] = int(paper_vertex)
			message = f"Paper {DOI} inserted into network. ({counter} of {total})"
			update_progress(message, "inserted")
			counter += 1
		except HTTPError:
			message = f"HTTPError ({counter} of {total})"
			update_progress(message, "fail")
			counter += 1
	return

def build_combined_graph(graph, DOIs):
	global vertex_dict
	global spinner

	spinner.start()
	cr = Crossref(mailto = "hwill12345@gmail.com")

	for DOI in DOIs:
		combined_process_paper(graph, DOI, cr)

	spinner.succeed("All papers inserted")
	spinner.start("Building citation edges...")

	for DOI in vertex_dict["paper"]:
		process_citations(graph, DOI, cr)

	spinner.stop()

options = ["network", "citation", "author", "user", "combined"]

print("Runtime Options Available")
for i in range(len(options)):
	print(str(i) + " - " + options[i])

program = options[int(input("Enter option number: "))]

data = DOIs[::1]
total = len(data)
counter = 1

vertex_dict = {"paper" : {}, "journal" : {}, "subject" : {}, "author" : {}, "user" : {}}
filename = input("Graph Filename [***].gt: ") + ".gt"
spinner = Halo(text = "Building network...", spinner = "runner", text_color = "red")

if program == "network":
	print("Running network program.")

	network_graph = create_network_graph()
	build_network_graph(network_graph, data)
	network_graph.save("./tmp/" + filename)
elif program == "citation":
	print("Running citation program.")

	citation_graph = create_citation_graph()
	build_citation_graph(citation_graph, data)
	citation_graph.save("./tmp/" + filename)
elif program == "author":
	print("Running author program.")

	author_graph = create_author_graph()
	build_author_graph(author_graph, data)
	author_graph.save("./tmp/" + filename)
elif program == "user":
	print("Running user program.")

	sqlite_cursor.execute("SELECT uni FROM ezproxy_users WHERE uni IS NOT NULL")
	users = [item[0] for item in sqlite_cursor.fetchall()]
	data = users[::1]

	total = len(data)

	user_graph = create_user_graph()
	build_user_graph(user_graph, data)
	user_graph.save("./tmp/" + filename)
elif program == "combined":
	print("Running combined program.")

	combined_graph = create_combined_graph()
	build_combined_graph(combined_graph, data)
	combined_graph.save("./tmp/" + filename)





