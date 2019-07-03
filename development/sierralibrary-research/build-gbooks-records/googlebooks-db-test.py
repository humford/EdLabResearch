import sys
import pprint
import sqlite3
import mysql.connector
import json
import re

from googleapiclient.discovery import build
from fuzzywuzzy import fuzz

api_key = "AIzaSyCAid0kMhZjasHpwIUjMWpM4h0uz4UP6tg"
service = build('books', 'v1', developerKey=api_key)

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def get_sierra_db():
	researchdb = mysql.connector.connect (
		host = "analytics.tc-library.org",
		user = "research",
		passwd = "S@YZfH",
		database = "research-sierra"
	)
	return researchdb

def setup_output_db(sqlite_cursor):
	sqlite_cursor.execute('''CREATE TABLE sierrabooks 
			(sierra_id INT, sierra_title TEXT, sierra_author TEXT, fixed_author TEXT, sierra_language TEXT, sierra_publish_year INT, google_title TEXT, title_sim INT, partial_title_sim INT, google_author TEXT, author_sim INT, partial_author_sim INT, google_category TEXT, google_json JSON)''')
	return

def get_bib_data(mysql_cursor):
	mysql_cursor.execute("SELECT * FROM bib")
	return mysql_cursor.fetchall()

def get_checkout_data(mysql_cursor):
	mysql_cursor.execute("SELECT * FROM checkout")
	return mysql_cursor.fetchall()

def get_checkout_books(mysql_cursor):
	checkout = get_checkout_data(mysql_cursor)
	books = []
	checkout_failure = []
	for item in checkout:
		if not item[2]:
			continue
		item_id = str(item[2])
		mysql_cursor.execute("SELECT bibIds FROM items WHERE id = %s", (item_id,))
		bib_entry = mysql_cursor.fetchone()
		if not bib_entry:
			checkout_failure.append(item_id)
		else:
			books.append(str(bib_entry[0]))
	return books, checkout_failure

def find_best_result(sierra_title, sierra_publish_year, items):
	top_match_score = 0
	top_match = {}
	for item in items:
		try:
			item_score = fuzz.partial_ratio(sierra_title, item["volumeInfo"]["title"])
		except KeyError:
			continue
		if item_score > top_match_score:
			top_match_score = item_score
			top_match = item
	return top_match

def fix_author(sierra_author):
	author_regex = r"^([^,]*), ([\w. ]*)(.*)"
	return re.sub(author_regex, "\\2 \\1", sierra_author, 0, re.MULTILINE)

def create_entry(sierra_id, sierra_title, sierra_author, sierra_language, sierra_publish_year, response):
	fixed_author = fix_author(sierra_author)
	try:
		google_title = response["volumeInfo"]["title"]
		title_sim = fuzz.ratio(sierra_title, google_title)
		title_partial_sim = fuzz.partial_ratio(sierra_title, google_title)
	except KeyError:
		google_title = ""
		title_sim = 0
		title_partial_sim = 0
	try:	
		google_author = str(response["volumeInfo"]["authors"][0])
		author_sim = fuzz.ratio(fixed_author, google_author)
		author_partial_sim = fuzz.partial_ratio(fixed_author, google_author)
	except KeyError:
		google_author = ""
		author_sim = 0
		author_partial_sim = 0
	try:
		google_category = str(response["volumeInfo"]["categories"][0])
	except KeyError:
		google_category = ""

	return (sierra_id, sierra_title, sierra_author, fixed_author, sierra_language, sierra_publish_year, 
		google_title, title_sim, title_partial_sim,
		google_author, author_sim, author_partial_sim,
		google_category, response)

def google_books_process(books, mysql_cursor, sqlite_cursor, STEP = 1, OFFSET = 1):
	MAX_INDEX = len(books)

	failure = []
	for i in range(MAX_INDEX):
		mysql_cursor.execute("SELECT * FROM bib WHERE id = %s", (books[i],))
		entry = mysql_cursor.fetchone()

		if not entry:
			failure.append(books[i])
			OFFSET -= 1
			continue

		print(entry)
		
		sierra_id = str(entry[0])
		sierra_title = entry[5]
		sierra_author = entry[1]
		sierra_language = entry[4]
		sierra_publish_year = entry[6]
		
		if not sierra_title:
			failure.append(sierra_id)
			OFFSET -= 1
			continue

		if sierra_author:
			fixed_author = fix_author(sierra_author)

		if sierra_author and not sierra_publish_year:
			query = str(sierra_title + " " + fixed_author)
		elif not sierra_author and sierra_publish_year:
			query = str(sierra_title + " " + str(sierra_publish_year))
		elif not sierra_author and not sierra_publish_year:
			query = str(sierra_title)
		else: 
			query = str(sierra_title + " " + fixed_author + " " + str(sierra_publish_year))

		if not sierra_author:
			#failure.append(sierra_id)
			#OFFSET -= 1
			#print("No author, skipping...")
			#continue
			sierra_author = ""
		if not sierra_publish_year:
			#failure.append(sierra_id)
			#OFFSET -= 1
			#print("No publish year, skipping...")
			#continue
			sierra_publish_year = ""

		sqlite_cursor.execute("SELECT google_json FROM sierrabooks WHERE sierra_id = ?", (sierra_id,))
		cache = sqlite_cursor.fetchone()

		found = False
		if cache:
			print(f"Found {sierra_id} in cache.")
			print(f"Finished {int(i / STEP) + OFFSET} of {int(MAX_INDEX / STEP) + OFFSET - 1}")
			continue
		else:
			# request = service.volumes().list(source='public', q=str("intitle:" + sierra_title + " inauthor:" + fixed_author), maxResults=1)
			print(query)
			request = service.volumes().list(source='public', q=query, maxResults=10)
			#try:
			if True:
				search = request.execute()
				if not search["totalItems"] == 0:
					response = find_best_result(sierra_title, sierra_publish_year, search["items"])
					print(response)
					found = True
				else:
					book = create_entry(sierra_id, sierra_title, sierra_author, sierra_language, sierra_publish_year, {"id" : "No Google Response"})
			# except Exception as error:
			# 	failure.append(sierra_id)
			# 	OFFSET -= 1
			# 	print(error)
			# 	print("API problem, skipping...")
			# 	continue
	
		if found:
			book = create_entry(sierra_id, sierra_title, sierra_author, sierra_language, sierra_publish_year, response)

		sqlite_cursor.execute("INSERT INTO sierrabooks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", book)

		print(f"Wrote item {sierra_id} to database")
		print(f"Finished {int(i / STEP) + OFFSET} of {int(MAX_INDEX / STEP) + OFFSET - 1}")

	print("Saving database...")
	conn.commit()
	conn.close()
	print("Saved")

	return failure

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

researchdb = get_sierra_db()
mysql_cursor = researchdb.cursor()

conn = sqlite3.connect("sierra-checkout-book.db")
sqlite_cursor = conn.cursor()

#books, checkout_failure = get_checkout_books(mysql_cursor)

books = ['1014954', '1024050', '1024452', '1024455', '1024478', '1024952', '1024955', '1025625', '1025676', '1025700', '1026155', '1026301', '1026455', '1027156', '1027479', '1027877', '1027920', '1028598', '1029289', '1030386', '1030553', '1030742', '1031226', '1032692', '1038540', '1039170', '1039786', '1040696', '1041568', '1041604', '1042240', '1042240', '1042745', '1043328', '1043893', '1043911', '1044272', '1044726', '1044756', '1045807', '1045987', '1046509', '1046802', '1047012', '1047073', '1047293', '1047414', '1048098', '1048435', '1048461', '1048494', '1048865', '1049410', '1049719', '1049770', '1050770', '1051138', '1051702', '1051771', '1051863', '1052145', '1052235', '1052471', '1052504', '1052778', '1052811', '1053122', '1053826', '1054186', '1055415', '1055433', '1058237', '1059547', '1060816', '1061748', '1062217', '1062733', '1063103', '1064176', '1065075', '1065823', '1067145', '1068283', '1069017', '1069037', '1069097', '1069166', '1069169', '1069191', '1069362', '1070049', '1070350', '1070409', '1070995', '1071197', '1071203', '1074880', '1075322', '1077018', '1078017', '1078108', '1078963', '1079239', '1079539', '1079842', '1079917', '1080281', '1080493', '1080565', '1081293', '1081574', '1081806', '1081957', '1082574', '1083320', '1083331', '1086163', '1086624', '1086698', '1087038', '1087246', '1087359', '1087407', '1087456', '1087841', '1088126', '1088377', '1088798', '1089210', '1090465', '1091488', '1093035', '1093238', '1093508', '1093634', '1093749', '1093857', '1094094', '1094172', '1094537', '1095485', '1095678', '1095842', '1095978', '1096043', '1096198', '1096576', '1096877', '1097159', '1097165', '1097173', '1098648', '1098832', '1099341', '1099574', '1099740', '1100168', '1100189', '1100913', '1101260', '1101555', '1102540', '1103801', '1104505', '1104509', '1105725', '1105738', '1106077', '1015088', '1021553', '1012173', '1037107', '1010624', '1000025', '1013133', '1020893', '1005961', '1004271', '1017732', '1033767', '1033915', '1034253', '1016595', '1016677', '1016724', '1006373', '1008688', '1019534', '1016984', '1032628', '1017172', '1017206', '1013409', '1004866', '1032898', '1033176', '1033192', '1019916', '1020146', '1006983', '1007002', '1007133', '1013562', '1039306', '1039310', '1039312', '1037163', '1037386', '1037577', '1035878', '1018500', '1041021', '1038074', '1034723', '1038128', '1036245', '1019135', '1005527', '1014310', '1021634', '1001229', '1007892', '1023513', '1015583', '1010256', '1009806', '1010812', '1111636', '1111670', '1111761', '1110926', '1105906', '1111422', '1112715', '1103241', '1113753', '1114168', '1116433', '1117414', '1117739', '1117857', '1117863', '1118318', '1118634', '1119655', '1120122', '1120611', '1120674', '1121877', '1121880', '1122910', '1123352', '1123489', '1123983', '1124550', '1126572', '1127975', '1129545', '1129849', '1002536', '1048461', '1027610', '1134252', '1134312', '1134524', '1134580', '1134736', '1134934', '1135086', '1136641', '1136988', '1137262', '1131599', '1133023', '1057107', '1140016', '1140324', '1137559', '1140578', '1001574', '1078097', '1099701', '1100133', '1086143', '1051139', '1072673', '1038125', '1083121', '1187535', '1099446', '1043775', '1036999', '1143118', '1143317', '1090879', '1082633', '1144127', '1144312', '1005264', '1124299', '1011574', '1145619', '1073536', '1119866', '1146254', '1103680', '1261071', '1113372', '1147712', '1032692', '1094753', '1082895', '1082370', '1052952', '1079640', '1151452', '1039418', '1123961', '1078503', '1067150', '1078731', '1147818', '1129443', '1045033', '1025388', '1147260', '1242962', '1151542', '1153153', '1076279', '1151625', '1289076', '1151628', '1017203', '1008113', '1158842', '1158908', '1045333', '1159273', '1159765', '1225154', '1157761', '1155978', '1160862', '1155943', '1156625', '1278201', '1109276', '1156692', '1152583', '1158479', '1159208', '1151793', '1259114', '1259116', '1013013', '1025121', '1159557', '1162099', '1164377', '1164376', '1288676', '1005167', '1164044', '1167094', '1278309', '1078103', '1160488', '1166904', '1047346', '1169392', '1265052', '1170240', '1165240', '1164102', '1167231', '1270340', '1169183', '1165987', '1163594', '1277321', '1163556', '1169688', '1155169', '1162989', '1163229', '1164116', '1096295', '1164104', '1161844', '1174047', '1173531', '1171371', '1171371', '1174628', '1025571', '1171679', '1166140', '1175707', '1039886', '1088670', '1176722', '1032866', '1176760', '1176498', '1177752', '1179319', '1050631', '1057607', '1256536', '1179822', '1171726', '1178703', '1182511', '1182701', '1182407', '1183221', '1181789', '1083777', '1180018', '1186017', '1185092', '1185785', '1183295', '1185857', '1183310', '1189221', '1288464', '1016731', '1186225', '1187096', '1187809', '1183672', '1187235', '1186744', '1187305', '1187763', '1187599', '1184032', '1188241', '1187746', '1187914', '1185906', '1125012', '1187208', '1189605', '1187749', '1196758', '1187425', '1190728', '1185759', '1190798', '1187975', '1191365', '1189829', '1191195', '1197519', '1186223', '1191520', '1189583', '1189365', '1189388', '1009691', '1191356', '1188221', '1269764', '1017105', '1199685', '1199897', '1200381', '1199338', '1124468', '1268759', '1191161', '1200910', '1278209', '1201481', '1199717', '1199092', '1201008', '1202352', '1201462', '1203795', '1204499', '1190413', '1201240', '1201445', '1204958', '1177489', '1204908', '1206142', '1199059', '1203177', '1207254', '1207925', '1258375', '1206866', '1205795', '1258515', '1206596', '1208950', '1203193', '1209825', '1209704', '1211740', '1211741', '1207637', '1209384', '1211384', '1211618', '1210192', '1213559', '1211630', '1211684', '1213135', '1219691', '1212578', '1224254', '1218817', '1264805', '1264675', '1211898', '1212128', '1211939', '1219534', '1224770', '1210799', '1226564', '1208799', '1228177', '1227394', '1228833', '1228380', '1043261', '1264306', '1228367', '1228725', '1155390', '1210848', '1230092', '1229994', '1229669', '1231351', '1230545', '1231856', '1232860', '1233472', '1234515', '1233204', '1229943', '1228330', '1232252', '1234864', '1218875', '1234698', '1234981', '1230176', '1231120', '1235567', '1228860', '1233544', '1071914', '1234721', '1235040', '1236631', '1243840', '1236965', '1236636', '1226368', '1237068', '1252021', '1256435', '1258079', '1259238', '1260248', '1263828', '1264355', '1264799', '1265427', '1266060', '1237089', '1206269', '1267205', '1267949', '1270015', '1270070', '1271143', '1271988', '1276127', '1277617', '1287614', '1290985', '1211903', '1207647', '1252066', '1093508', '1236253', '1122910', '1236789', '1295328', '1231639', '1229974', '1231635', '1252064', '1295547', '1295547', '1235042', '1295182', '1237016', '1236775', '1233542', '1303296', '1295799', '1235031', '1236363', '1295971', '1303323', '1296971', '1303220', '1205407', '1302797', '1305683', '1315510', '1325253', '1328032', '1336521', '1336521', '1351419', '1354649', '1304235', '1237178', '1304288', '1303193', '1228056', '1230043', '1364225', '1303310', '1303593', '1363031', '1363316', '1364099', '1304870', '1235269', '1302917', '1365681', '1365683', '1303121', '1363940', '1366263', '1366263', '1366263', '1365045', '1364735', '1302830', '1304904', '1367633', '1364331', '1304809', '1366080', '1366488', '1367862', '1364869', '1366449', '1157761', '1304780', '1366112', '1366340', '1219581', '1364648', '1367597', '1366002', '1368104', '1368524', '1368148', '1368954', '1364964', '1369836', '1368315', '1395660', '1370693', '1212219', '1304905', '1304903', '1367995', '1366554', '1368464', '1370506', '1399076', '1197519', '1132545', '1398907', '1398896', '1369909', '1365026', '1370580', '1038027', '1370188', '1364342', '1364342', '1132652', '1399925', '1366266', '1400816', '1399063', '1256889', '1401537', '1401142', '1401977', '1401205', '1402765', '1121852', '1402669', '1092569', '1403496', '1401726', '1402695', '1402689', '1399584', '1404214', '1212349', '1269611', '1404118', '1406616', '1406088', '1406338', '1406755', '1407163', '1406933', '1407066', '1408459', '1410960', '1410622', '1410354', '1409575', '1411568', '1411342', '1411062', '1410831', '1411862', '1412028', '1414854', '1413212', '1412586', '1413132', '1414052', '1212172', '1414407', '1414551', '1414742', '1415344', '1416446', '1416014', '1412214', '1416030', '1417503', '1416872', '1366352', '1414779', '1420776', '1422099', '1422601', '1422976', '1423076', '1423360', '1423248', '1423275', '1399590', '1423119', '1423582', '1422946', '1178336', '1423711', '1422829', '1423982', '1424232', '1424826', '1424826', '1424826', '1424826', '1424826', '1423920', '1425652', '1425875', '1426833', '1425036', '1424660', '1427064', '1427831', '1426073', '1428289', '1422613', '1424429', '1427564', '1424447', '1424972', '1427164', '1428027', '1428146', '1428139', '1427594', '1425906', '1430812', '1430869', '1430339', '1429025', '1432163', '1432156', '1430997', '1432236', '1432652', '1433883', '1431400', '1433885', '1431319', '1432056', '1433796', '1434078', '1430330', '1431841', '1431988', '1434090', '1434079', '1431685', '1434183', '1433930', '1434601', '1431835', '1433287', '1434421', '1434552', '1435680', '1435723', '1435595', '1436413', '1434575', '1436403', '1401205', '1435889', '1437422', '1434695', '1436203', '1437245', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1437192', '1435609', '1437626', '1437542', '1436965', '1436965', '1437691', '1437845', '1437885', '1437966', '1437697', '1437997', '1438089', '1438762', '1439098', '1438528', '1451693', '1437717', '1451840', '1453095', '1453097', '1453014', '1452814', '1438140', '1451863', '1439071', '1453300', '1439059', '1452722', '1437908', '1453398', '1453347', '1438164', '1439059', '1456916', '1456964', '1469887', '1469990', '1453169', '1453473', '1453222', '1423993', '1236785', '1453488', '1470910', '1471088', '1470755', '1470793', '1470413', '1471298', '1470945', '1471393', '1471393', '1470707', '1471170', '1471602', '1471865', '1471812', '1471991', '1472737', '1472271', '1472898', '1472915', '1406937', '1473435', '1473539', '1430963', '1473819', '1473605', '1472794', '1473880', '1473603', '1473620', '1516641', '1522422', '1522394', '1522429', '1522562', '1528880', '1522677', '1535795', '1528889', '1535898', '1536075', '1544096', '1536263', '1536271', '1536254', '1553487', '1561051', '1561064', '1566904', '1566928', '1553283', '1567789', '1574945', '1581267', '1574573', '1581214', '1574508', '1174240', '1587812', '1581193', '1587609', '1588004', '1593909', '1602463', '1602040', '1605713', '1613129', '1613453', '1612956', '1613217', '1613232', '1613517', '1630272', '1522422', '1553372', '1646590', '1646645', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1522422', '1655474', '1665355', '1656798', '1666151', '1674694', '1674694', '1674694', '1674694', '1674694', '1683162', '1683204', '1674718', '1674718', '1683333', '1683333', '1683333', '1699203', '1699239', '1699320', '1708619', '1708572', '1717040', '1716896', '1726280', '1717576', '1734540', '1743384', '1734472', '1735540', '1427831', '1747885', '1748084', '1749067', '1797600', '1471812', '1803550', '1803973', '1804101', '1811211', '1811205', '1432378', '1811472', '1811610', '1811718', '1813582', '1820107', '1820107', '1820107', '1820107', '1820275', '1821583', '1820370', '1835395', '1841551', '1890557', '1230986', '1229833', '1230515', '1574553', '1001317', '1197070', '1197070', '1199487', '1202139', '1427831', '1090222', '1267126', '1048266', '1083321', '1522422', '1522422', '1522422', '1522422', '1522422', '1121776', '1472325', '1921371', '1131850', '1434716', '1370272', '1835680', '1898607', '1898025', '1819790', '1036165', '1020040', '1083442', '1452661', '1923903', '1605728', '1811166', '1412590', '1847687', '1438359', '1411818', '1853495', '1368562', '1005648', '1185958', '1516641', '2065019', '1039968', '1039968', '1432104', '2087033', '1068785', '2088493', '2089346', '2088763', '2064756', '2065321', '1276395', '1033321', '1553639', '1438634', '1188080', '1050046', '1613122', '1365809', '1015579', '2061697', '1188080', '1262666', '1262665', '1121970', '1045636', '1122014', '2068165', '1303205', '1561078', '1432552', '1040414', '1431756', '1231105', '1036260', '1058156', '1272700', '2285002', '1128081', '1406192', '1427450', '1257860', '1551381', '1471722', '2287531', '2287531', '2287531', '2287531', '1242909', '1242909', '1923912', '2060365', '2289149', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1068590', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1142108', '1811166', '1811166', '1811166', '1033606', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1403325', '1811166', '1811166', '1811166', '1811166', '1187292', '1811166', '1811166', '1811166', '1811166', '1228489', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1255430', '1811166', '1811166', '1811166', '1811166', '1006060', '1128081', '1160482', '1811166', '1211250', '1811166', '1015579', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166', '1811166']

#print(len(books))
bib_failure = google_books_process(books, mysql_cursor, sqlite_cursor)

print(bib_failure)

