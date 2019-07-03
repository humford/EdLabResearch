# Import Configuration
from config import config

output_dir = config["OUTPUT"]["DIRECTORY"]
output_db = config["OUTPUT"]["DATABASE"]
crossref_email = config["API"]["CROSSREF_EMAIL"]

# Import Internal
from db_utils import *

# Import External


# MAIN