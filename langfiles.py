"""
Keeps track of the original and pending langfiles and ensures that any missing files get downloaded.
"""
import json
import os
import langfile_downloader
import download_pending

# download en_us.json if it doesn't exist
if not os.path.isfile('cache/lang/wurst/en_us.json'):
	print("Downloading en_us.json from Wurst...")
	langfile_downloader.download_langfile_wurst("en_us")

# load original as dict
with open('cache/lang/wurst/en_us.json', encoding='utf-8') as f:
	original = json.load(f)

# check if pending.json exists
if not os.path.isfile('pending.json'):
	url = input("No pending translation found. To download it from a pull request, please enter the URL: ")
	if url:
		download_pending.download_pending(url)
	else:
		exit()

# load pending as dict
with open('pending.json', encoding='utf-8') as f:
	pending = json.load(f)

# load langcode
with open('pending_lang.txt', encoding='utf-8') as f:
	langcode = f.read().strip()
	langcode_short = langcode.split('_')[0]