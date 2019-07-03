# Import Configuration
from config import config

output_dir = config["OUTPUT"]["DIRECTORY"]

# Import External
import re

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