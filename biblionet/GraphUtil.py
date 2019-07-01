class GraphUtil:
	"""docstring for GraphUtil"""
	def __init__(self):
		self.test = "test"

	def find_vertex_by_id(item_id, graph):
		for v in graph.get_vertices():
			if graph.vp.id[v] == item_id:
				return graph.vertex(v)

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
		