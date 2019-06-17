import mysql.connector

researchdb = mysql.connector.connect (
	host = "analytics.tc-library.org",
	user = "research",
	passwd = "S@YZfH",
	database = "ezproxy-logs-oclc"
)

cursor = researchdb.cursor()
cursor.execute("SELECT * FROM ezporxy_spu")
result = cursor.fetchall()

for item in result:
	if item[4] != None and item[4] != "":
		print(item[4])

# ^([^,]*), ([\w. ]*)(.*)