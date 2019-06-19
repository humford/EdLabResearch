# Build Visualizations from .gt File
import re
import cairo
from graph_tool.all import *
from os import listdir
from os.path import isfile, join
from halo import Halo

files = [f for f in listdir("./tmp/") if isfile(join("./tmp/",f)) and re.search(r"(.*\.gt)", f)]

print("Graph Files Available")
for i in range(len(files)):
	print(str(i) + " - " + files[i])

file_to_load = files[int(input("Enter file number: "))]

with Halo(text='Loading graph file...', spinner='dots'):
    graph = load_graph("./tmp/" + file_to_load)


#state = minimize_nested_blockmodel_dl(graph, deg_corr = True)
#draw_hierarchy(state, output = "nested_mdl.png")

# Get number of members for each item
num_members = graph.new_vp("int")
graph.vp["num_members"] = num_members

graph.vp.num_members.a = graph.get_in_degrees(graph.get_vertices())

# Clear empty vertices
del_list = []
for vertex in graph.vertices():
	if vertex.in_degree() == 0:
		if vertex.out_degree() == 0:
			del_list.append(vertex)
graph.remove_vertex(reversed(sorted(del_list)))

# Max members item

# m = 0
# for i in graph.get_vertices():
# 	vertex = graph.vertex(i)
# 	if vertex.in_degree() > m:
# 		m = vertex.in_degree()
# 		max_vertex = vertex
# print(max_vertex, m)

# Create standard graph visual
with Halo(text='Drawing visuals...', text_color = "red", spinner='monkey'):
	#vertex_size = prop_to_size(
	#	graph.vp.num_members
	#)
	#pos = arf_layout(graph, max_iter = 0)
	# graph_draw(graph, 
	# 	vertex_text = graph.vp.id, 
	# 	pos = pos,
	# 	output_size = (10000,10000), 
	# 	vertex_font_size = 18, 
	# 	vertex_shape = "square", 
	# 	bg_color = [1,1,1,1], 
	# 	vertex_fill_color = graph.vp.type, 
	# 	output = "arf.pdf"
	# )
	graph_draw(graph, 
		edge_pen_width = 0.1,
		#pos = pos,
		vertex_text = graph.vp.id,
		vorder = graph.vp.type,
		vertex_aspect = 1,
		vertex_text_position = 1,
		vertex_text_color = "black",
		vertex_font_family = "sans",
		vertex_font_size = 1,
		vertex_font_weight = cairo.FONT_WEIGHT_NORMAL,
		vertex_fill_color = graph.vp.type,
		vertex_size = 1,
		output = "./tmp/citation_test.pdf"
	)

# with Halo(text='Drawing Fruchterman Reingold...', text_color = "green", spinner='dots'):
# 	pos = fruchterman_reingold_layout(graph, n_iter=1000)
# 	graph_draw(graph, pos=pos, output="graph-draw-fr.pdf")

# with Halo(text='Drawing ARF...', text_color = "blue", spinner='dots'):
# 	pos = arf_layout(graph, max_iter = 0)
# 	graph_draw(graph, pos=pos, output="arf.pdf", vertex_text = graph.vp.type,
# 		vertex_fill_color = graph.vp.type, output_size = (10000,10000))


