"""
Downloads language files from Mojang's servers, InventivetalentDev's GitHub repo, and the Wurst7 GitHub repo. Also provides a function to load a merged dict for any given language.
"""
import requests
import json
import os

manifest_data = None

def get_manifest():
	global manifest_data
	if manifest_data is None:
		# Fetch the version manifest
		manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
		manifest_response = requests.get(manifest_url)
		manifest_data = json.loads(manifest_response.text)
	return manifest_data

def get_latest_version():
	manifest_data = get_manifest()
	# Find the ID for the latest version
	version_data = manifest_data['latest']['release']
	return version_data

def get_version_url(version):
	manifest_data = get_manifest()
	# Find the URL for the specified version
	version_data = next((item for item in manifest_data['versions'] if item["id"] == version), None)
	if version_data is None:
		print(f"Failed to find version {version}.")
		return None
	return version_data['url']

def check_lang_dir():
	# Create the lang directories if they don't exist
	if not os.path.exists('cache/lang/wurst'):
		os.makedirs('cache/lang/wurst')
	if not os.path.exists('cache/lang/mc'):
		os.makedirs('cache/lang/mc')

def download_langfile_official(version, lang_code):
	check_lang_dir()

	# Fetch the version data
	version_url = get_version_url(version)
	if version_url is None:
		return
	version_response = requests.get(version_url)
	version_data = json.loads(version_response.text)

	# Fetch the asset index
	asset_index_url = version_data['assetIndex']['url']
	asset_index_response = requests.get(asset_index_url)
	asset_index_data = json.loads(asset_index_response.text)

	# Find the hash for the language file
	lang_file_hash = asset_index_data['objects'][f'minecraft/lang/{lang_code}.json']['hash']

	# Construct the URL for the language file
	lang_file_url = f"https://resources.download.minecraft.net/{lang_file_hash[:2]}/{lang_file_hash}"

	# Download the language file
	lang_file_response = requests.get(lang_file_url)
	if lang_file_response.status_code == 200:
		with open(f"cache/lang/mc/{lang_code}.json", 'wb') as f:
			f.write(lang_file_response.content)
		print(f"Successfully downloaded {lang_code}.json from official Mojang servers.")
	else:
		print(f"WARNING: Failed to download {lang_code}.json from official Mojang servers.")
		print(f"URL: {lang_file_url}")
		print(f"Status Code: {lang_file_response.status_code}")
		print(f"Response Content: {lang_file_response.content}")

def download_langfile_unofficial(version, lang_code):
	check_lang_dir()
	url = f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/{version}/assets/minecraft/lang/{lang_code}.json"
	response = requests.get(url)
	if response.status_code == 200:
		with open(f"cache/lang/mc/{lang_code}.json", 'wb') as f:
			f.write(response.content)
		print(f"Successfully downloaded {lang_code}.json from InventivetalentDev.")
	else:
		print(f"WARNING: Failed to download {lang_code}.json from InventivetalentDev.")
		print(f"URL: {url}")
		print(f"Status Code: {response.status_code}")
		print(f"Response Content: {response.content}")

def download_langfile_wurst(lang_code):
	check_lang_dir()
	url = f"https://raw.githubusercontent.com/Wurst-Imperium/Wurst7/master/src/main/resources/assets/wurst/lang/{lang_code}.json"
	response = requests.get(url)
	if response.status_code == 200:
		with open(f"cache/lang/wurst/{lang_code}.json", 'wb') as f:
			f.write(response.content)
		print(f"Successfully downloaded {lang_code}.json from Wurst.")
	# else:
	# 	print(f"WARNING: Failed to download {lang_code}.json from Wurst.")
	#	print(f"URL: {url}")
	#	print(f"Status Code: {response.status_code}")
	#	print(f"Response Content: {response.content}")

def load_merged_langfile(language):
	# download mc language file if it doesn't exist
	if not os.path.exists(f"cache/lang/mc/{language}.json"):
		version = get_latest_version()
		if language == "en_us":
			download_langfile_unofficial(version, language)
		else:
			download_langfile_official(version, language)

	# download wurst language file if it doesn't exist
	if not os.path.exists(f"cache/lang/wurst/{language}.json"):
		download_langfile_wurst(language)

	# load language files
	with open(f"cache/lang/mc/{language}.json", "r", encoding="utf-8") as f:
		mc_lang = json.load(f)
	if os.path.exists(f"cache/lang/wurst/{language}.json"):
		with open(f"cache/lang/wurst/{language}.json", "r", encoding="utf-8") as f:
			wurst_lang = json.load(f)
	else:
		wurst_lang = {}

	# return merged language files, with wurst language file taking priority
	lang_data = {**mc_lang, **wurst_lang}
	return lang_data
