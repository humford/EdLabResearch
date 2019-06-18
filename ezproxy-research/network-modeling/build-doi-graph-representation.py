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

from graph_tool.all import *
from habanero import Crossref
from requests.exceptions import HTTPError

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
	# types: paper, journal, subject
	item_type = network_graph.new_vertex_property("string")
	network_graph.vp.type = item_type

	return network_graph

def process_subjects(network_graph, subjects):
	global vertex_dict
	subject_vertices = []

	for subject in subjects:
		if subject["ASJC"] in vertex_dict["subject"]:
			subject_index = vertex_dict["subject"][subject["ASJC"]]
			subject_vertex = network_graph.vertex(subject_index)
			subject_vertices.append(subject_vertex)
			print("Subject " + str(subject["ASJC"]) + " found in network.")
		else:
			subject_vertex = network_graph.add_vertex()
			network_graph.vp.id[subject_vertex] = subject["ASJC"]
			network_graph.vp.name[subject_vertex] = subject["name"]
			network_graph.vp.type[subject_vertex] = "subject"

			vertex_dict["subject"][subject["ASJC"]] = int(subject_vertex)
			subject_vertices.append(subject_vertex)
			print(f"Subject " + str(subject["ASJC"]) + " inserted into network.")
	return subject_vertices

def process_journal(network_graph, journal):
	global vertex_dict
	subjects = journal["subjects"]
	subject_vertices = process_subjects(network_graph, subjects)
	ISSN = journal["ISSN"][0]

	if ISSN in vertex_dict["journal"]:
		journal_index = vertex_dict["journal"][ISSN]
		journal_vertex = network_graph.vertex(journal_index)
		print(f"Journal " + ISSN + " found in network.")
	else:
		journal_vertex = network_graph.add_vertex()
		network_graph.vp.id[journal_vertex] = ISSN
		network_graph.vp.name[journal_vertex] = journal["title"][0]
		network_graph.vp.type[journal_vertex] = "journal"

		for subject_vertex in subject_vertices:
			network_graph.add_edge(journal_vertex, subject_vertex)

		vertex_dict["journal"][ISSN] = int(journal_vertex)
		print("Journal " + ISSN + " inserted into network.")
	return journal_vertex


def process_paper(network_graph, DOI, cr):
	global vertex_dict
	item = cr.works(ids = DOI)
	title = item["message"]["title"][0]

	if DOI in vertex_dict["paper"]:
		print(f"Paper {DOI} found in network.")
	else:
		try:
			journal = cr.journals(ids = item["message"]["ISSN"])
			if "message" in journal:
				journal = journal["message"]
			elif type(journal) == type(list()):
				journal = journal[0]["message"]
			else:
				print(f"No journal found for paper {DOI}.")
				return
			
			journal_vertex = process_journal(network_graph, journal)

			paper_vertex = network_graph.add_vertex()
			network_graph.vp.id[paper_vertex] = DOI
			network_graph.vp.name[paper_vertex] = title
			network_graph.vp.type[paper_vertex] = "paper"

			network_graph.add_edge(paper_vertex, journal_vertex)

			vertex_dict["paper"][DOI] = int(paper_vertex)
			print(f"Paper {DOI} inserted into network.")
		except HTTPError:
			print("HTTPError")
	return

def build_network_graph(network_graph, DOIs):
	cr = Crossref(mailto = "htw2116@columbia.edu")

	for DOI in DOIs:
		process_paper(network_graph, DOI, cr)
	print("Network built.")

vertex_dict = {"paper" : {}, "journal" : {}, "subject" : {}}
network_graph = create_network_graph()
print(network_graph.list_properties())

build_network_graph(network_graph, DOIs[1:100])

graph_draw(network_graph, vertex_text = network_graph.vp.id, 
           output_size = (2500,2500), vertex_font_size = 18, vertex_shape = "square", 
           bg_color = [1,1,1,1], output = "network_graph.png")

pos = arf_layout(network_graph, max_iter = 0)
graph_draw(network_graph, pos=pos, output="arf.pdf", vertex_text = network_graph.vp.id)

