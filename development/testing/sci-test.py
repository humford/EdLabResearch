from scihub import SciHub

sh = SciHub()

# fetch specific article (don't download to disk)
# this will return a dictionary in the form 
# {'pdf': PDF_DATA,
# 'url': SOURCE_URL
# }
result = sh.fetch('http://ieeexplore.ieee.org/xpl/login.jsp?tp=&arnumber=1648853')

with open('output.pdf', 'wb+') as fd:
	fd.write(result['pdf'])
