# import yaml

# with open("config.yaml", "r") as yamlfile:
# 	config = yaml.load(yamlfile, Loader=yaml.FullLoader)

config = {
	'API': {
		'CROSSREF_EMAIL': 'htw2116@columbia.edu',
        'GOOGLE_API_KEY': 'AIzaSyCAid0kMhZjasHpwIUjMWpM4h0uz4UP6tg'},
	'DATABASES': {
		'EZPROXY_DB': {
			'DATABASE': 'ezproxy-logs-oclc',
            'HOST': 'analytics.tc-library.org',
            'PASSWD': 'S@YZfH',
            'USER': 'research'},
    'LIBRARY_SIERRA_DB': {
    		'DATABASE': 'research-sierra',
            'HOST': 'analytics.tc-library.org',
            'PASSWD': 'S@YZfH',
            'USER': 'research'}},
	'OUTPUT': {
		'DATABASE': 'ezproxy-DOI.db',
        'DIRECTORY': '/Users/henrywilliams/Git/EdLabResearch/output/'}
}