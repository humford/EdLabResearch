# Import Configuration
from config import config

output_dir = config["OUTPUT"]["DIRECTORY"]
output_db = config["OUTPUT"]["DATABASE"]
crossref_email = config["API"]["CROSSREF_EMAIL"]

# Import Internal
from graph_utils import *
from db_utils import *

# Import External
from graph_tool.all import *
from halo import Halo
from habanero import Crossref
from requests.exceptions import HTTPError, ConnectionError
from pprint import pprint
from time import sleep

# MAIN

# Update progress on spinner
def update_progress(message, status, spinner):
	if status == "inserted":
		spinner.succeed(message)
	elif status == "found":
		spinner.info(message)
	elif status == "fail":
		spinner.fail(message)
	spinner.start("Building network...")

# GRAPH CREATION

# Make structure graph
def create_structure_graph(directed = True):
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

# Create user graph
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

# ITEM PROCESSING

# Process the authors for a paper
def process_authors(graph, authors, spinner):
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
			update_progress(message, "found", spinner)
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
			update_progress(message, "inserted", spinner)
	return author_vertices

# Process the subjects for a journal
def process_subjects(graph, subjects, spinner):
	global vertex_dict

	subject_vertices = []

	for subject in subjects:
		if subject["ASJC"] in vertex_dict["subject"]:
			subject_index = vertex_dict["subject"][subject["ASJC"]]
			subject_vertex = graph.vertex(subject_index)
			subject_vertices.append(subject_vertex)

			message = "Subject " + str(subject["ASJC"]) + " found in network."
			update_progress(message, "found", spinner)
		else:
			subject_vertex = graph.add_vertex()
			graph.vp.id[subject_vertex] = subject["ASJC"]
			graph.vp.name[subject_vertex] = subject["name"]
			graph.vp.type[subject_vertex] = 0

			vertex_dict["subject"][subject["ASJC"]] = int(subject_vertex)
			subject_vertices.append(subject_vertex)

			message = "Subject " + str(subject["ASJC"]) + " inserted into network."
			update_progress(message, "inserted", spinner)
	return subject_vertices

# Process the journal for a paper
def process_journal(graph, journal, spinner):
	global vertex_dict

	subjects = journal["subjects"]
	subject_vertices = process_subjects(graph, subjects, spinner)
	ISSN = journal["ISSN"][0]

	if ISSN in vertex_dict["journal"]:
		journal_index = vertex_dict["journal"][ISSN]
		journal_vertex = graph.vertex(journal_index)

		message = "Journal " + ISSN + " found in network."
		update_progress(message, "found", spinner)
	else:
		journal_vertex = graph.add_vertex()
		graph.vp.id[journal_vertex] = ISSN
		if type(journal["title"]) == type(list()):
			title = journal["title"][0]
		else:
			title = journal["title"]
		graph.vp.name[journal_vertex] = title
		graph.vp.type[journal_vertex] = 1

		for subject_vertex in subject_vertices:
			graph.add_edge(journal_vertex, subject_vertex)

		vertex_dict["journal"][ISSN] = int(journal_vertex)

		message = "Journal " + ISSN + " inserted into network."
		update_progress(message, "inserted", spinner)
	return journal_vertex

# Process a paper
def process_paper(graph, DOI, cr, mode, counter, total, spinner):
	global vertex_dict

	try:
		item = cr.works(ids = DOI)
	except HTTPError:
		message = f"HTTPError ({counter} of {total})"
		update_progress(message, "fail", spinner)
		return None
	except TimeoutError:
		message = f"TimeoutError ({counter} of {total})"
		update_progress(message, "fail", spinner)
		return None

	if not item["message"]["title"]:
		message = f"Paper {DOI} no title found ({counter} of {total})"
		update_progress(message, "fail", spinner)
		return None
	title = item["message"]["title"][0]

	if DOI in vertex_dict["paper"]:
		message = f"Paper {DOI} found in network. ({counter} of {total})"
		update_progress(message, "found", spinner)
		return None
	else:
		try:
			author_vertices = []
			journal_vertex = None

			if mode in ["author", "combined"]:
				if not "author" in item["message"]:
					message = f"Paper {DOI} no authors found ({counter} of {total})"
					update_progress(message, "fail", spinner)
					return None
				elif not item["message"]["author"]:
					message = f"Paper {DOI} no authors found ({counter} of {total})"
					update_progress(message, "fail", spinner)
					return None
				authors = item["message"]["author"]

				author_vertices = process_authors(graph, authors, spinner)

			if mode in ["network", "combined"]:
				if not "ISSN" in item["message"]:
					return None
				try:
					journal = cr.journals(ids = item["message"]["ISSN"])
				except HTTPError:
					sleep(5)
					message = f"HTTPError ({counter} of {total})"
					update_progress(message, "fail", spinner)
					return None
				except ConnectionError:
					sleep(5)
					message = f"ConnectionError ({counter} of {total})"
					update_progress(message, "fail", spinner)
					return None
				except TimeoutError:
					sleep(5)
					message = f"TimeoutError ({counter} of {total})"
					update_progress(message, "fail", spinner)
					return None

				if "message" in journal:
					journal = journal["message"]
				elif type(journal) == type(list()):
					journal = journal[0]["message"]
				else:
					message = f"No journal found for paper {DOI}. ({counter} of {total})"
					update_progress(message, "fail", spinner)
					return None
				
				journal_vertex = process_journal(graph, journal, spinner)
			
			paper_vertex = graph.add_vertex()
			graph.vp.id[paper_vertex] = DOI
			graph.vp.name[paper_vertex] = title
			graph.vp.type[paper_vertex] = 2
			vertex_dict["paper"][DOI] = int(paper_vertex)

			if journal_vertex:
				graph.add_edge(paper_vertex, journal_vertex)

			if author_vertices:
				for author_vertex in author_vertices:
					author_edge = graph.add_edge(author_vertex, paper_vertex)
					author = graph.vp.author_info[author_vertex]
					if author["sequence"] == "first":
						graph.ep.author_type[author_edge] = 1
					else:
						graph.ep.author_type[author_edge] = 0

			message = f"Paper {DOI} inserted into network. ({counter} of {total})"
			update_progress(message, "inserted", spinner)
			return paper_vertex
		except HTTPError:
			message = f"HTTPError ({counter} of {total})"
			update_progress(message, "fail", spinner)
			return None

# Process the citations for a paper
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

# Process user
def process_user(graph, uni, cr, counter, total, spinner):
	global vertex_dict
	global sqlite_cursor

	sqlite_cursor.execute("SELECT ezproxy_user_id FROM ezproxy_users WHERE uni = ?", (uni,))
	user_id = sqlite_cursor.fetchone()[0]

	sqlite_cursor.execute("SELECT ezproxy_doi_id FROM access_records WHERE ezproxy_doi_id = ?", (user_id,))
	records = [item[0] for item in sqlite_cursor.fetchall()]

	if uni in vertex_dict["user"]:
		message = f"User {uni} found in network. ({counter} of {total})"
		user_vertex = vertex_dict["user"][uni]
		user_vertex = graph.vertex(user_index)
		update_progress(message, "found", spinner)
	else:
		user_vertex = graph.add_vertex()
		graph.vp.id[user_vertex] = uni
		graph.vp.name[user_vertex] = user_id
		graph.vp.type[user_vertex] = 4

		vertex_dict["user"][uni] = int(user_vertex)
		message = f"User {uni} inserted into network. ({counter} of {total})"
		update_progress(message, "inserted", spinner)

	for record in records:
		sqlite_cursor.execute("SELECT doi FROM ezproxy_doi WHERE ezproxy_doi_id = ?", (record,))
		try:
			DOI = sqlite_cursor.fetchone()[0]
		except TypeError:
			continue

		paper_vertex = process_paper(graph, DOI, cr, "user", counter, total, spinner)
		if paper_vertex:
			prior_access_edge = graph.edge(user_vertex, paper_vertex)
			if prior_access_edge:
				graph.ep.times_accessed[prior_access_edge] += 1
			else:
				access_edge = graph.add_edge(user_vertex, paper_vertex)
				graph.ep.times_accessed[access_edge] = 1
	return

# GRAPH BUILDING

# Build a graph based on metadata structure
def build_structure_graph(graph, DOIs, mode, spinner):
	global crossref_email
	global vertex_dict
	vertex_dict = {"paper" : {}, "journal" : {}, "subject" : {}, "author" : {}}

	total = len(DOIs)
	counter = 1

	spinner.start()
	cr = Crossref(mailto = crossref_email)

	for DOI in DOIs:
		process_paper(graph, DOI, cr, mode, counter, total, spinner)
		counter += 1
	spinner.succeed("All papers inserted")

	if mode in ["citation", "combined"]:
		spinner.start("Building citation edges...")

		for DOI in vertex_dict["paper"]:
			process_citations(graph, DOI, cr)

		spinner.stop()

# Build a graph based on user access records
def build_user_graph(graph, users, spinner, cursor):
	global crossref_email
	global vertex_dict
	global sqlite_cursor
	sqlite_cursor = cursor

	vertex_dict = {"paper" : {}, "journal" : {}, "subject" : {}, "author" : {}, "user" : {}}

	total = len(users)
	counter = 1

	spinner.start()
	cr = Crossref(mailto = crossref_email)

	for uni in users:
		process_user(graph, uni, cr, counter, total, spinner)
		counter += 1

	spinner.succeed("All users inserted")

# WRAPPERS

# Wrapper routine for different graph types
def network_routine():
	options = ["network", "citation", "author", "user", "combined"]

	print("Runtime Options Available")
	for i in range(len(options)):
		print(str(i) + " - " + options[i])

	program = options[int(input("Enter option number: "))]

	filename = input("Graph Filename [*].[gt, graphml, etc]: ")
	spinner = Halo(text = "Building network...", spinner = "runner", text_color = "red")

	add_json_to_output_db()
	conn = connect_to_output_db()
	sqlite_cursor = conn.cursor()

	if program == "user":
		sqlite_cursor.execute("SELECT uni FROM ezproxy_users WHERE uni IS NOT NULL")
		data = [item[0] for item in sqlite_cursor.fetchall()]
		print("Running user program.")

		graph = create_user_graph()
		build_user_graph(graph, data[:10:], spinner, sqlite_cursor)
	else:
		sqlite_cursor.execute("SELECT doi FROM ezproxy_doi WHERE doi IS NOT NULL")
		data = [item[0] for item in sqlite_cursor.fetchall()]

		graph = create_structure_graph()
		if program == "network":
			print("Running network program.")
		elif program == "citation":
			print("Running citation program.")
		elif program == "author":
			print("Running author program.")
		elif program == "combined":
			print("Running combined program.")

		build_structure_graph(graph, data[:10:], program, spinner)
	graph.save(output_dir + filename)
	print("Graph saved.")