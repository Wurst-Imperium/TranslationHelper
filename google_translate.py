"""
Does the forward and reverse translations using Google Translate. Only reverse is shown in the table, but both are used for evaluations.
"""
import json
import os
from tqdm import tqdm
from googletrans import Translator
import pycountry
from langfiles import original, pending, langcode_short

translator = Translator()

# Create the cache directory if it doesn't exist
if not os.path.exists('cache/google_translate'):
	os.makedirs('cache/google_translate')

def forward_translate(dest):
	langname = pycountry.languages.get(alpha_2=dest).name
	print(f"Google-translating en_us.json to {langname}...")
	translations = {}
	for key, value in tqdm(original.items()):
		translations[key] = translator.translate(value, src='en', dest=dest).text
		with open('cache/google_translate/forward.json', 'w', encoding='utf-8') as f:
			json.dump(translations, f, indent=2)
	return translations

def reverse_translate(src):
	langname = pycountry.languages.get(alpha_2=src).name
	print(f"Revere-translating pending.json from {langname}...")
	translations = {}
	for key, value in tqdm(pending.items()):
		translations[key] = translator.translate(value, src=src, dest='en').text
		with open('cache/google_translate/reverse.json', 'w', encoding='utf-8') as f:
			json.dump(translations, f, indent=2)
	return translations

original_mtime = os.path.getmtime('cache/lang/wurst/en_us.json')
pending_mtime = os.path.getmtime('pending.json')

# check if forward.json exists
if not os.path.isfile('cache/google_translate/forward.json'):
	forward = forward_translate(langcode_short)
# check if forward.json is older than en_us.json
elif os.path.getmtime('cache/google_translate/forward.json') < original_mtime:
	forward = forward_translate(langcode_short)
# load forward.json as dict
else:
	with open('cache/google_translate/forward.json', encoding='utf-8') as f:
		forward = json.load(f)

# check if reverse.json exists
if not os.path.isfile('cache/google_translate/reverse.json'):
	reversed = reverse_translate(langcode_short)
# check if reverse.json is older than pending.json
elif os.path.getmtime('cache/google_translate/reverse.json') < pending_mtime:
	reversed = reverse_translate(langcode_short)
# load reverse.json as dict
else:
	with open('cache/google_translate/reverse.json', encoding='utf-8') as f:
		reversed = json.load(f)

del original_mtime, pending_mtime