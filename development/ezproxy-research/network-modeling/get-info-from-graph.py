import re
import cairo
from graph_tool.all import *
from os import listdir
from os.path import isfile, join
from halo import Halo

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

def find_vertex_by_id(item_id, graph):
    for v in graph.get_vertices():
        if graph.vp.id[v] == item_id:
            return graph.vertex(v)

def find_all_x_for_y(x_type, y, graph):
    vertices = []
    vertex = find_vertex_by_id(y, graph)
    y_type = graph.vp.type[vertex]
    
    diff = y_type - x_type
    
    if diff == 3:
        for parent in vertex.out_neighbors():
            for pparent in parent.out_neighbors():
                for ppparent in pparent.out_neighbors():
                    if graph.vp.type[ppparent] == x_type:
                        vertices.append(ppparent)
    elif diff == 2:
        for parent in vertex.out_neighbors():
            for pparent in parent.out_neighbors():
                if graph.vp.type[pparent] == x_type:
                    vertices.append(pparent)
    elif diff == 1:
        for parent in vertex.out_neighbors():
            if graph.vp.type[parent] == x_type:
                vertices.append(parent)
    elif diff == 0:
        for parent in vertex.out_neighbors():
            for child in parent.in_neighbors():
                if graph.vp.type[child] == x_type:
                    vertices.append(child)
    elif diff == -1:
        for child in vertex.in_neighbors():
            if graph.vp.type[child] == x_type:
                vertices.append(child)
    elif diff == -2:
        for child in vertex.in_neighbors():
            for cchild in child.in_neighbors():
                if graph.vp.type[cchild] == x_type:
                    vertices.append(cchild)
    elif diff == -3:
        for child in vertex.in_neighbors():
            for cchild in child.in_neighbors():
                for ccchild in cchild.in_neighbors():
                    if graph.vp.type[ccchild] == x_type:
                        vertices.append(ccchild)
    else:
        raise
    return vertices

def display_vertices(vertices, graph):
    types = ['subject', 'journal', 'paper', 'author'] 
    for v in vertices:
        print(f"Type: {types[graph.vp.type[v]]}; ID: {graph.vp.id[v]}; Name: {graph.vp.name[v]}")

graph = get_graph_from_folder()
vertices = find_all_x_for_y(2, "1200", graph)
display_vertices(vertices, graph)