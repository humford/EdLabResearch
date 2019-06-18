from habanero import Crossref
from pprint import pprint
from graph_tool.all import *

cr = Crossref(mailto = "htw2116@columbia.edu")

n = 50
journal_ISSN = "1471-2105"
journal_papers = cr.journals(ids = journal_ISSN, works = True, limit = n)

def print_paper_info(journal_papers):
    for paper in journal_papers["message"]["items"]:
        print("Title: " + paper["title"][0])
        print("DOI: " + paper["DOI"])
        first_author = None
        for author in paper["author"]:
            if author["sequence"] == "first":
                first_author = author["given"] + " " + author["family"]
                break
        print("First Author: " + first_author)

journal_graph = Graph()
vertex_id = journal_graph.new_vertex_property("string")

journal_root = journal_graph.add_vertex()
vertex_id[journal_root] = journal_ISSN

for paper in journal_papers["message"]["items"]:
    paper_vertex = journal_graph.add_vertex()
    vertex_id[paper_vertex] = paper["DOI"]
    journal_graph.add_edge(paper_vertex, journal_root)

journal_graph.vp.id = vertex_id
graph_draw(journal_graph, vertex_text = journal_graph.vp.id, 
           output_size = (750,750), vertex_font_size = 5, vertex_shape = "square", 
           bg_color = [1,1,1,1], output = "journal_graph.png")

state = minimize_nested_blockmodel_dl(journal_graph, deg_corr = True)
draw_hierarchy(state, output = "nested_mdl.pdf")

pos = arf_layout(journal_graph, max_iter = 0)
graph_draw(journal_graph, pos=pos, output="arf.pdf")

pos = sfpd_layout(journal_graph)
graph_draw(journal_graph, pos=pos, output="sfpd.pdf")