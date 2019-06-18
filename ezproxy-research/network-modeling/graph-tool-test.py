from graph_tool.all import *
from habanero import Crossref


def get_journal_papers(ISSN):
	cr = Crossref(mailto = "htw2116@columbia.edu")
	cr.journals()

g = Graph()

ug = Graph(directed = False)

g1 = Graph(g)

v1 = g.add_vertex()
v2 = g.add_vertex()

e = g.add_edge(v1, v2)

print(e.source(), e.target())

vlist = g.add_vertex(10)

graph_draw(g, vertex_text = g.vertex_index, vertex_font_size = 18, output_size = (200,200), output = "two-nodes.png", bg_color = [1,1,1,1])


