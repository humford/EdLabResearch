import dash
import dash_cytoscape as cyto 
import dash_html_components as html
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

elements = []

for v in graph.get_vertices():
	this = {"data" : {"id" : v, "label" : graph.vp.id[v]}}
	elements.append(this)

for e in graph.edges():
	this = {"data" : {"source" : int(e.source()), "target" : int(e.target()), "label" : f"Node {str(e.source())} to {str(e.target())}"}}
	elements.append(this)

cyto.load_extra_layouts()

app = dash.Dash(__name__)
app.layout = html.Div([
	cyto.Cytoscape(
		id = "cytoscape",
		elements = elements,
        layout={'name': 'dagre'}
	)
])

if __name__ == "__main__":
	app.run_server(debug = True)