from webweb import Web
from graph_tool.all import *
from os import listdir
from os.path import isfile, join
from halo import Halo
import re

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

graph = get_graph_from_folder()

#graph = extract_largest_component(graph, directed = False, prune = True)

edge_list = graph.get_edges(
	#eprops = [graph.ep.author_type]
)

for edge in edge_list:
	edge[2] += 1

display={
    "nodes" : {},
    'metadata' : {
        'type' : {
            'categories' : ['subject', 'journal', 'paper', 'author'],
        },
    },
}

size = [10,5,1,0.5]
categories = ['subject', 'journal', 'paper', 'author']

for v in graph.get_vertices():
    node_values = {
        "id" : graph.vp.id[v],
        "name" : graph.vp.name[v],
        "type" : graph.vp.type[v],
        "type_size" : size[graph.vp.type[v]],
    }
    display["nodes"][v] = node_values

web = Web(
    adjacency = edge_list,
    display = display
)

web.show()