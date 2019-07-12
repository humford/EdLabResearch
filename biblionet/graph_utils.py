# Import Configuration
from .config import config

output_dir = config["OUTPUT"]["DIRECTORY"]

# Import External
import re
import cairo
import matplotlib

from graph_tool.all import *
from os import listdir
from os.path import isfile, join
from halo import Halo

# MAIN

#Print all vertices
def display_vertices(vertices, graph):
    types = ['subject', 'journal', 'paper', 'author', 'user'] 
    for v in vertices:
        print(f"Type: {types[graph.vp.type[v]]}; ID: {graph.vp.id[v]}; Name: {graph.vp.name[v]}")

#Get vertex by id
def find_vertex_by_id(item_id, graph):
	for v in graph.get_vertices():
		if graph.vp.id[v] == item_id:
			return graph.vertex(v)

# Get graph from file
def get_graph_from_folder():
	files = [f for f in listdir(output_dir) if isfile(join(output_dir,f)) and re.search(r"(.*\.gt)", f)]
	print("Graph Files Available")
	for i in range(len(files)):
		print(str(i) + " - " + files[i])

	file_to_load = files[int(input("Enter file number: "))]

	with Halo(text='Loading graph file...', spinner='dots'):
		graph = load_graph(output_dir + file_to_load)

	return graph

# Convert graph file in output dir
def convert_filetype():
	graph = get_graph_from_folder()
	filename = input("Filename to convert to: ") 
	
	graph.save(output_dir + filename)

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

	#pos = graphviz_draw(graph, vsize=10, overlap=False, output=None)

	with Halo(text='Drawing visuals...', text_color = "red", spinner='bouncingBall'):
		graph_draw(graph,
			#pos = pos, 
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
			output = output_dir + filename
		)

def plain_visual_routine(type_size = False):
	graph = get_graph_from_folder()
	draw_plain_visual(graph, input("Plain visual filename: "), type_size = type_size)
