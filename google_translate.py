"""
Does the forward and reverse translations using Google Translate. Only reverse is shown in the table, but all three are used for evaluations.
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

def forward_translate(lang):
	langname = pycountry.languages.get(alpha_2=lang).name
	print(f"Google-translating en_us.json to {langname}...")
	translations = {}
	for key, value in tqdm(original.items()):
		translations[key] = translator.translate(value, src='en', dest=lang).text
		with open('cache/google_translate/forward.json', 'w', encoding='utf-8') as f:
			json.dump(translations, f, indent=2)
	return translations

def reverse_translate_pending(lang):
	langname = pycountry.languages.get(alpha_2=lang).name
	print(f"Revere-translating pending.json from {langname}...")
	translations = {}
	for key, value in tqdm(pending.items()):
		translations[key] = translator.translate(value, src=lang, dest='en').text
		with open('cache/google_translate/reverse.json', 'w', encoding='utf-8') as f:
			json.dump(translations, f, indent=2)
	return translations

"""
Translates the Google-translated original strings back to English to
intentionally introduce errors. This makes them easier to compare with the
reverse-translated strings, because both sets should have the same Google
Translate artifacts.
"""
def reverse_translate_forward(forward, lang):
	langname = pycountry.languages.get(alpha_2=lang).name
	print(f"Revere-translating forward.json from {langname}...")
	translations = {}
	for key, value in tqdm(forward.items()):
		translations[key] = translator.translate(value, src=lang, dest='en').text
		with open('cache/google_translate/forward_reverse.json', 'w', encoding='utf-8') as f:
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
	reversed = reverse_translate_pending(langcode_short)
# check if reverse.json is older than pending.json
elif os.path.getmtime('cache/google_translate/reverse.json') < pending_mtime:
	reversed = reverse_translate_pending(langcode_short)
# load reverse.json as dict
else:
	with open('cache/google_translate/reverse.json', encoding='utf-8') as f:
		reversed = json.load(f)

# check if forward_reverse.json exists
if not os.path.isfile('cache/google_translate/forward_reverse.json'):
	forward_reverse = reverse_translate_forward(forward, langcode_short)
# check if forward_reverse.json is older than forward.json
elif os.path.getmtime('cache/google_translate/forward_reverse.json') < os.path.getmtime('cache/google_translate/forward.json'):
	forward_reverse = reverse_translate_forward(forward, langcode_short)
# load forward_reverse.json as dict
else:
	with open('cache/google_translate/forward_reverse.json', encoding='utf-8') as f:
		forward_reverse = json.load(f)

del original_mtime, pending_mtime

gt_identical = set()
gt_reversible = set()
gt_reversible_artifacts = set()

for key in original.keys():
	if key not in pending:
		continue
	if pending[key].lower() == forward[key].lower():
		gt_identical.add(key)
	if original[key].lower() == reversed[key].lower():
		gt_reversible.add(key)
	if reversed[key].lower() == forward_reverse[key].lower():
		gt_reversible_artifacts.add(key)

gt_same_meaning = gt_identical | gt_reversible | gt_reversible_artifacts
