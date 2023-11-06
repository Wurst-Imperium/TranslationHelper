"""
A small utility script to check how Minecraft translates a given string.
"""
import i18n
import sys
from langfiles import langcode

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: python check_mc_translation.py <string>")
		exit()
	
	english = " ".join(sys.argv[1:])
	keys = i18n.reverse_lookup_multi(english)

	for key in keys:
		print(f"Key: {key}")
		translated = i18n.translate(key, langcode)
		print(f"Value: {translated}")
