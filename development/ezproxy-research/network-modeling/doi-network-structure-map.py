from graph_tools.all import *

doi_network = Graph()
vertex_id = doi_network.new_vertex_property("string")
doi_network.vp.id = vertex_id

doi_network.new_vertex()