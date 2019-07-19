# Import Configuration
from config import config

output_dir = config["OUTPUT"]["DIRECTORY"]
output_db = config["OUTPUT"]["DATABASE"]
crossref_email = config["API"]["CROSSREF_EMAIL"]

# Import Internal
from db_utils import *

# Import External
from timeit import default_timer as timer

start = timer()
end = timer()
print(f"X takes {end - start} seconds to run.")

# MAIN

def add_ezproxy_logs_to_db():
	pass

def ezproxy_db_routine():
	ezproxy_conn = connect_to_ezproxy_db()
	ezproxy_cursor = ezproxy_conn.cursor()
	setup_ezproxy_spu_table(ezproxy_cursor)

	