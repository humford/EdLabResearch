import metaknowledge as mk
import networkx as nx 
import matplotlib.pyplot as plt 
import metaknowledge.contour.plotting as mkv

RC = mk.RecordCollection('./tmp/savedrecs.txt')

CoCitation = RC.networkCoCitation()

print(mk.graphStats(CoCitation, makeString = True))

# print(CoCitation.nodes(data = True)[0])

# print(CoCitation.edges(data = True)[0])

coCiteJournals = RC.networkCoCitation(nodeType = 'journal', dropNonJournals = True)
print(mk.graphStats(coCiteJournals))

nx.draw_spring(coCiteJournals)
