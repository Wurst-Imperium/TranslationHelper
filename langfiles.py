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
	if langcode == "zh_cn":
		langcode_short = "zh-cn"
	elif langcode == "zh_tw":
		langcode_short = "zh-tw"
	else:
		langcode_short = langcode.split('_')[0]

# try to download old translation
if not os.path.isfile(f'cache/lang/wurst/{langcode}.json'):
	print(f"Downloading {langcode}.json from Wurst...")
	langfile_downloader.download_langfile_wurst(langcode)

# try to load old translation
if os.path.isfile(f'cache/lang/wurst/{langcode}.json'):
	with open(f'cache/lang/wurst/{langcode}.json', encoding='utf-8') as f:
		old_translation = json.load(f)
else:
	old_translation = {}

# remove pending strings that are identical to the old translation
for key in list(pending.keys()):
	if key in old_translation and pending[key] == old_translation[key]:
		pending.pop(key)
