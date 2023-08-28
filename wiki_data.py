"""
Loads the wiki data export file, either from the current directory or directly from Wurst if the Wurst folder location has been specified in .env.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()
if "WURST_FOLDER" not in os.environ:
	file_path = "wiki-data.json"
else:
	file_path = os.path.join(os.environ["WURST_FOLDER"], "wiki-data.json")

with open(file_path, "r", encoding="utf-8") as f:
	wiki_data = json.load(f)
