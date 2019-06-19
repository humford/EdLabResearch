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
from requests.exceptions import HTTPError

def create_citation_graph(directed = True):
	citation_graph = Graph(directed = directed)
	# ID
	# types: DOI, ISSN, ASJC code
	item_id = citation_graph.new_vertex_property("string")
	citation_graph.vp.id = item_id

	# Name
	# types: paper title, journal name, subject name
	item_name = citation_graph.new_vertex_property("string")
	citation_graph.vp.name = item_name

	# Type
	# types: paper (2), journal (1), subject (0)
	item_type = citation_graph.new_vertex_property("int")
	citation_graph.vp.type = item_type

	return citation_graph

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
	network_graph = Graph()
	# ID
	# types: DOI, ISSN, ASJC code
	item_id = network_graph.new_vertex_property("string")
	network_graph.vp.id = item_id

	# Name
	# types: paper title, journal name, subject name
	item_name = network_graph.new_vertex_property("string")
	network_graph.vp.name = item_name

	# Type
	# types: paper (2), journal (1), subject (0)
	item_type = network_graph.new_vertex_property("int")
	network_graph.vp.type = item_type

	return network_graph

def update_progress(message, status):
	global spinner

	if status == "inserted":
		spinner.succeed(message)
	elif status == "found":
		spinner.info(message)
	elif status == "fail":
		spinner.fail(message)
	spinner.start("Building network...")	 

def process_subjects(network_graph, subjects):
	global vertex_dict

	subject_vertices = []

	for subject in subjects:
		if subject["ASJC"] in vertex_dict["subject"]:
			subject_index = vertex_dict["subject"][subject["ASJC"]]
			subject_vertex = network_graph.vertex(subject_index)
			subject_vertices.append(subject_vertex)

			message = "Subject " + str(subject["ASJC"]) + " found in network."
			update_progress(message, "found")
		else:
			subject_vertex = network_graph.add_vertex()
			network_graph.vp.id[subject_vertex] = subject["ASJC"]
			network_graph.vp.name[subject_vertex] = subject["name"]
			#network_graph.vp.type[subject_vertex] = "subject"
			network_graph.vp.type[subject_vertex] = 0

			vertex_dict["subject"][subject["ASJC"]] = int(subject_vertex)
			subject_vertices.append(subject_vertex)

			message = "Subject " + str(subject["ASJC"]) + " inserted into network."
			update_progress(message, "inserted")
	return subject_vertices

def process_journal(network_graph, journal):
	global vertex_dict

	subjects = journal["subjects"]
	subject_vertices = process_subjects(network_graph, subjects)
	ISSN = journal["ISSN"][0]

	if ISSN in vertex_dict["journal"]:
		journal_index = vertex_dict["journal"][ISSN]
		journal_vertex = network_graph.vertex(journal_index)

		message = "Journal " + ISSN + " found in network."
		update_progress(message, "found")
	else:
		journal_vertex = network_graph.add_vertex()
		network_graph.vp.id[journal_vertex] = ISSN
		network_graph.vp.name[journal_vertex] = journal["title"][0]
		#network_graph.vp.type[journal_vertex] = "journal"
		network_graph.vp.type[journal_vertex] = 1

		for subject_vertex in subject_vertices:
			network_graph.add_edge(journal_vertex, subject_vertex)

		vertex_dict["journal"][ISSN] = int(journal_vertex)

		message = "Journal " + ISSN + " inserted into network."
		update_progress(message, "inserted")
	return journal_vertex

def process_paper(network_graph, DOI, cr):
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
			journal = cr.journals(ids = item["message"]["ISSN"])
			if "message" in journal:
				journal = journal["message"]
			elif type(journal) == type(list()):
				journal = journal[0]["message"]
			else:
				message = f"No journal found for paper {DOI}. ({counter} of {total})"
				update_progress(message, "fail")
				counter += 1
				return
			
			journal_vertex = process_journal(network_graph, journal)

			paper_vertex = network_graph.add_vertex()
			network_graph.vp.id[paper_vertex] = DOI
			network_graph.vp.name[paper_vertex] = title
			#network_graph.vp.type[paper_vertex] = "paper"
			network_graph.vp.type[paper_vertex] = 2

			network_graph.add_edge(paper_vertex, journal_vertex)

			vertex_dict["paper"][DOI] = int(paper_vertex)
			message = f"Paper {DOI} inserted into network. ({counter} of {total})"
			update_progress(message, "inserted")
			counter += 1
		except HTTPError:
			message = f"HTTPError ({counter} of {total})"
			update_progress(message, "fail")
			counter += 1
	return

def build_network_graph(network_graph, DOIs):
	global spinner
	
	spinner.start()
	cr = Crossref(mailto = "htw2116@columbia.edu")

	for DOI in DOIs:
		process_paper(network_graph, DOI, cr)
	spinner.stop()

	print("Network built.")

vertex_dict = {"paper" : {}, "journal" : {}, "subject" : {}}
network_graph = create_network_graph()
#citation_graph = create_citation_graph()

data = DOIs[::1]
total = len(data)
counter = 1

filename = input("Graph Filename [***].gt: ") + ".gt"

spinner = Halo(text = "Building network...", spinner = "runner", text_color = "red")
build_network_graph(network_graph, data)
#build_citation_graph(citation_graph, data)

network_graph.save("./tmp/" + filename)
#citation_graph.save("./tmp/" + filename)




