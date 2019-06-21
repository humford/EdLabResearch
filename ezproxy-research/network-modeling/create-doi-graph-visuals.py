# Build Visualizations from .gt File
import re
import cairo
import matplotlib
from graph_tool.all import *
from os import listdir
from os.path import isfile, join
from halo import Halo

# Find max members item
def find_max_member_item(graph):
	m = 0
	for i in graph.get_vertices():
		vertex = graph.vertex(i)
		if vertex.in_degree() > m:
			m = vertex.in_degree()
			max_vertex = vertex
	return max_vertex, m

# Get number of members for each item
def add_num_members_property(graph):
	num_members = graph.new_vp("int")
	graph.vp["num_members"] = num_members

	graph.vp.num_members.a = graph.get_in_degrees(graph.get_vertices())

	return graph

# Get size by type
def add_size_by_type(graph):
	sizes = [5,2.5,1]
	size = graph.new_vp("int")
	graph.vp.size = size

	for v in graph.get_vertices():
		graph.vp.size[v] = sizes[graph.vp.type[v]]

	return graph

# Get graph from file
def get_graph_from_folder():
	files = [f for f in listdir("./tmp/") if isfile(join("./tmp/",f)) and re.search(r"(.*\.gt)", f)]

	print("Graph Files Available")
	for i in range(len(files)):
		print(str(i) + " - " + files[i])

	file_to_load = files[int(input("Enter file number: "))]

	with Halo(text='Loading graph file...', spinner='dots'):
		graph = load_graph("./tmp/" + file_to_load)

	return graph

# Clear empty vertices
def clear_empty_vertices(graph):
	del_list = []
	for vertex in graph.vertices():
		if vertex.in_degree() == 0:
			if vertex.out_degree() == 0:
				del_list.append(vertex)
	graph.remove_vertex(reversed(sorted(del_list)))
	return graph

# Draw best partition
def draw_best_partition(graph, filename = "bestpartition.pdf"):
	#graph.set_directed(False)
	with Halo(text="Calculating partition...", text_color = "blue", spinner = "moon"):
		state = minimize_blockmodel_dl(graph)

	with Halo(text='Drawing visuals...', text_color = "red", spinner='bouncingBall'):
		state.draw(
			vertex_shape = state.get_blocks(),
			output = f"./tmp/{filename}"
		)

def draw_condensation_graph(graph, filename = "condensation.pdf", n = 20):
	with Halo(text="Calculating partition...", text_color = "blue", spinner = "moon"):
		state = BlockState(graph, B = n, deg_corr = True)
		mcmc_equilibrate(state, wait = 1000)
		b = state.get_blocks()
	with Halo(text='Drawing visuals...', text_color = "red", spinner='bouncingBall'):
		bg, bb, vcount, ecount, avp, aep = condensation_graph(
			graph,
			b,
			avprops = [sfdp_layout(graph)],
			self_loops = True
		)
		pos = avp[0]

		for v in bg.vertices():
			pos[v].a /= vcount[v]

		graph_draw(
			bg, 
			pos = avp[0],
			vertex_fill_color = bb,
			vertex_shape = bb,
			vertex_size = prop_to_size(vcount, mi = 40, ma = 100),
			edge_pen_width = prop_to_size(ecount, mi = 2, ma = 10),
			output = "./tmp/blocks_cond.pdf"
		)

		graph_draw(
			graph,
			vertex_fill_color = b,
			vertex_shape = b,
			vertex_size = 1,
			edge_pen_width = 0.5,
			output = f"./tmp/{filename}"
		)

# Draw closeness
def draw_closeness(graph, filename = "closeness.pdf"):
	graph = GraphView(graph, vfilt = label_largest_component(graph))
	c = closeness(graph)

	graph_draw(graph,
		vertex_fill_color = c,
		vertex_size = prop_to_size(c, mi = 5, ma = 15),
		vcmap = matplotlib.cm.gist_heat,
		vorder = c,
		output = f"./tmp/{filename}"
	)

# Get Jaccard similarity
def draw_similarity(graph, filename = "similarity.pdf", style = "jaccard"):
	graph.set_directed(False)

	with Halo(text="Calculating similarity...", text_color = "blue", spinner = "moon"):
		s = vertex_similarity(graph, style)
	
	#max_vertex, m = find_max_member_item(graph)
	color = graph.new_vp("double")
	color.a = s[96].a
	
	with Halo(text='Drawing visuals...', text_color = "red", spinner='bouncingBall'):
		graph_draw(graph, 
			vertex_text = graph.vertex_index,
			vertex_color = color,
			vertex_fill_color = color,
			vertex_aspect = 1,
			edge_pen_width = 0.5,
			vertex_size = 1,
			vertex_font_size = 1,
			vcmap = matplotlib.cm.inferno,
			output = f"./tmp/{filename}"
		)

# Create non-standard graph visual
def draw_special_visual(graph, filename, include_id = False, layout = "sfdp"):
	graph.set_directed(False)

	if include_id:
		vertex_text = graph.vp.id
	else:
		vertex_text = ""

	with Halo(text="Making layout...", text_color = "blue", spinner = "moon"):
		if layout == "sfdp":
			pos = sfdp_layout(graph)
		elif layout == "arf":
			pos = arf_layout(graph, max_iter = 0)
		elif layout == "fruchterman_reingold":
			pos = fruchterman_reingold_layout(graph, n_iter=1000)
		elif layout == "radial":
			max_vertex, m = find_max_member_item(graph)
			pos = radial_tree_layout(graph, max_vertex)
		elif layout == "random":
			pos = random_tree_layout(graph)

	with Halo(text='Drawing visuals...', text_color = "red", spinner='bouncingBall'):
		graph_draw(graph, 
			edge_pen_width = 0.1,
			pos = pos,
			vertex_text = vertex_text,
			vorder = graph.vp.type,
			vertex_aspect = 1,
			vertex_text_position = 1,
			vertex_text_color = "black",
			vertex_font_family = "sans",
			vertex_font_size = 1,
			vertex_font_weight = cairo.FONT_WEIGHT_NORMAL,
			vertex_fill_color = graph.vp.type,
			vertex_size = 1,
			output = f"./tmp/{filename}"
		)

def special_visual_routine(graph):
	layouts = ["sfdp", "arf", "fruchterman_reingold", "radial", "random"]
	print("Layout Options Available")
	for i in range(len(layouts)):
		print(str(i) + " - " + layouts[i])

	layout = layouts[int(input("Enter option number: "))]

	draw_special_visual(graph, input("Special visual filename: "), layout = layout)


# Create standard graph visual
def draw_plain_visual(graph, filename, include_id = False, type_size = False):
	if include_id:
		vertex_text = graph.vp.id
	else:
		vertex_text = ""

	if type_size:
		vertex_size = graph.vp.size
	else:
		vertex_size = 1

	pos = graphviz_draw(graph, vsize=10, overlap=False, output=None)

	with Halo(text='Drawing visuals...', text_color = "red", spinner='bouncingBall'):
		graph_draw(graph,
			pos = pos, 
			edge_pen_width = 0.1,
			vertex_text = vertex_text,
			vorder = graph.vp.type,
			vertex_aspect = 1,
			vertex_text_position = 1,
			vertex_text_color = "black",
			vertex_font_family = "sans",
			vertex_font_size = 0.2,
			vertex_font_weight = cairo.FONT_WEIGHT_NORMAL,
			vertex_fill_color = graph.vp.type,
			vertex_size = vertex_size,
			output = f"./tmp/{filename}"
		)

def plain_visual_routine(graph, type_size = False):
	draw_plain_visual(graph, input("Plain visual filename: "), type_size = type_size)

def draw_graphviz_visual(graph, filename):
	if not filename:
		filename = "graphviz-draw.pdf"

	with Halo(text='Drawing visuals...', text_color = "red", spinner='monkey'):
		graphviz_draw(graph, 
			vcolor=graph.vp.type, 
			vorder=graph.vp.type, 
			elen=10, 
			size=(30,30),
			overlap="prism10000",
			splines=True,
			penwidth=0.5,
			#ecolor=ebet, 
			#eorder=ebet, 
			output = f"./tmp/{filename}"
		)

def graphviz_routine(graph):
	draw_graphviz_visual(graph, input("Graphviz filename: "))

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


graph = get_graph_from_folder()
#graph = clear_empty_vertices(graph)
graph = extract_largest_component(graph, directed = False, prune = True)
#graph = add_size_by_type(graph)
draw_condensation_graph(graph)

# with Halo(text='Drawing Fruchterman Reingold...', text_color = "green", spinner='dots'):
# 	pos = fruchterman_reingold_layout(graph, n_iter=1000)
# 	graph_draw(graph, pos=pos, output="graph-draw-fr.pdf")

# with Halo(text='Drawing ARF...', text_color = "blue", spinner='dots'):
# 	pos = arf_layout(graph, max_iter = 0)
# 	graph_draw(graph, pos=pos, output="arf.pdf", vertex_text = graph.vp.type,
# 		vertex_fill_color = graph.vp.type, output_size = (10000,10000))


