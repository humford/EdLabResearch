from graph_tool.all import *
from os import listdir
from os.path import isfile, join
from halo import Halo
import re

# Get graph from file
def get_graph_from_folder(message = "Enter file number: "):
	files = [f for f in listdir("./tmp/") if isfile(join("./tmp/",f)) and re.search(r"(.*\.gt)", f)]

	print("Graph Files Available")
	for i in range(len(files)):
		print(str(i) + " - " + files[i])

	file_to_load = files[int(input(message))]

	with Halo(text='Loading graph file...', spinner='dots'):
		graph = load_graph("./tmp/" + file_to_load)

	return graph

def combine_graphs():
	graph1 = get_graph_from_folder(message = "Choose first file: ")
	graph2 = get_graph_from_folder(message = "Choose second file: ")
	filename = input("Filename of combined file: ") 

	graph = graph_union(graph1, 
		graph2, 
		intersection = graph2.vp.id,
		props = [
			(graph1.vp.id, graph2.vp.id),
			(graph1.vp.name, graph2.vp.name),
			(graph1.vp.type, graph2.vp.type)
		]
	)

	graph.save("./tmp/" + filename)

def convert_filetype():
	graph = get_graph_from_folder()
	filename = input("Filename to convert to: ") 
	
	graph.save("./tmp/" + filename)

convert_filetype()