"""
Provides functions for translating and reverse-translating strings using Minecraft's and Wurst's language files.
"""
import langfile_downloader

lang_data = {}

def translate(key, language="en_us", fallback=None):
	# load language file if it hasn't been loaded yet
	if not language in lang_data:
		lang_data[language] = langfile_downloader.load_merged_langfile(language)

	# return translation or fallback
	return lang_data[language].get(key, key if fallback is None else fallback)

def reverse_lookup(value, language="en_us", fallback=None):
	# load language file if it hasn't been loaded yet
	if not language in lang_data:
		lang_data[language] = langfile_downloader.load_merged_langfile(language)

	# try to find a matching value
	for key, val in lang_data[language].items():
		if val.lower() == value.lower():
			return key

	# if no match is found, return fallback
	return value if fallback is None else fallback

def reverse_lookup_multi(value, language="en_us", fallback=None):
	# load language file if it hasn't been loaded yet
	if not language in lang_data:
		lang_data[language] = langfile_downloader.load_merged_langfile(language)

	# try to find matching values
	keys = []
	for key, val in lang_data[language].items():
		if val.lower() == value.lower():
			keys.append(key)
	
	# if no match is found, return fallback
	return keys if fallback is None else fallback
