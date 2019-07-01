# Get DOIs from ezproxy
import sqlite3
import matplotlib.pyplot as plt

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def trim_to_first_n(l, n):
	l = l[:n] + [""] * (len(l) - n)
	return l

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("../ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

sqlite_cursor.execute("SELECT ezproxy_user_id FROM ezproxy_users WHERE ezproxy_user_id IS NOT NULL")
users = [item[0] for item in sqlite_cursor.fetchall()]

# for user in users:
# 	sqlite_cursor.execute("SELECT ezproxy_doi_id FROM access_records WHERE ezproxy_user_id = ?", (user,))
# 	records = [item[0] for item in sqlite_cursor.fetchall()]
# 	subjects = []
# 	for record in records:
# 		sqlite_cursor.execute("SELECT subject_id FROM doi_subjects WHERE ezproxy_doi_id = ?", (record,))
# 		subject_ids = [item[0] for item in sqlite_cursor.fetchall()]
# 		for subject_id in subject_ids:
# 			sqlite_cursor.execute("SELECT subject FROM subjects WHERE subject_id = ?", (subject_id,))
# 			subjects.append(sqlite_cursor.fetchone()[0])
# 	subjects = list(set(subjects))
# 	sqlite_cursor.execute("SELECT uni FROM ezproxy_users WHERE ezproxy_user_id = ?", (user,))
# 	message = f"User: {sqlite_cursor.fetchone()[0]}; Subjects: {subjects}"
# 	print(message)

access_subjects = {}

sqlite_cursor.execute("SELECT subject_id FROM subjects WHERE subject_id IS NOT NULL")
subjects = [item[0] for item in sqlite_cursor.fetchall()]

for subject_id in subjects:
	sqlite_cursor.execute("SELECT ezproxy_doi_id FROM doi_subjects WHERE subject_id = ?", (subject_id,))
	items = [item[0] for item in sqlite_cursor.fetchall()]
	users = {}
	for item in items:
		sqlite_cursor.execute("SELECT ezproxy_user_id FROM access_records WHERE ezproxy_doi_id = ?", (item,))
		user_ids = [item[0] for item in sqlite_cursor.fetchall()]
		for user_id in user_ids:
			sqlite_cursor.execute("SELECT uni FROM ezproxy_users WHERE ezproxy_user_id = ?", (user_id,))
			user = sqlite_cursor.fetchone()[0]
			if user in users:
				users[user] += 1
			else:
				users[user] = 1
	sqlite_cursor.execute("SELECT subject from subjects WHERE subject_id = ?", (subject_id,))
	#message = f"Subject: {sqlite_cursor.fetchone()[0]}; Users: {sum(users.values())}"
	#print(message)
	access_subjects[sqlite_cursor.fetchone()[0]] = sum(users.values())

sorted_access_subjects = sorted(access_subjects.items(), key=lambda kv: kv[1], reverse=True)

labels = trim_to_first_n([item[0] for item in sorted_access_subjects], 15)
sizes = [item[1] for item in sorted_access_subjects]

fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, autopct="%1.1f%%", shadow=False, startangle=90)
ax1.axis("equal")

plt.show()
