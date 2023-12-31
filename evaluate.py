"""
This is what adds all the errors, warnings, etc. that you see in the table. More complex evaluations are done in separate files and imported here.
"""
import datetime
import json
import os
import re
from langfiles import original, pending, old_translation
from google_translate import forward, gt_identical, gt_reversible, gt_reversible_artifacts, gt_same_meaning
from wiki_data import wiki_data
from gpt_extract_mcnames import mcnames
from gpt_embeddings import low_distance_any, get_low_distance_message
import namefinder

# define evals and helper functions
evals = {}
def add_error(key, message):
	if key not in evals:
		evals[key] = {"errors": []}
	elif "errors" not in evals[key]:
		evals[key]["errors"] = []
	evals[key]["errors"].append(message)
def add_warning(key, message):
	if key not in evals:
		evals[key] = {"warnings": []}
	elif "warnings" not in evals[key]:
		evals[key]["warnings"] = []
	evals[key]["warnings"].append(message)
def add_info(key, message):
	if key not in evals:
		evals[key] = {"info": []}
	elif "info" not in evals[key]:
		evals[key]["info"] = []
	evals[key]["info"].append(message)
def add_good_sign(key, message):
	if key not in evals:
		evals[key] = {"good_signs": []}
	elif "good_signs" not in evals[key]:
		evals[key]["good_signs"] = []
	evals[key]["good_signs"].append(message)

# add timestamp
add_info("_general_", f"This analysis was generated on {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}.")

# check for untranslated strings
for key in original.keys():
	if key not in pending:
		if key in old_translation:
			add_info(key, "Skipped this string because it's identical to the old translation.")
		else:
			add_info(key, "This string has not been translated.")
			add_info(key, f"Google translation: {forward[key]}")
	elif original[key] == pending[key]:
		add_error(key, "This string is still in English.")

# check for strings that don't exist in the original
new_strings = pending.keys() - original.keys()
for key in new_strings:
	add_error(key, "This string does not exist in the original.")
if len(new_strings) > 0:
	add_error("_general_", f"The translation contains {len(new_strings)} strings that don't exist in the original.")

# check order of strings
original_keys_present_in_pending = [key for key in original.keys() if key in pending]
pending_keys_present_in_original = [key for key in pending.keys() if key in original]
if original_keys_present_in_pending != pending_keys_present_in_original:
	add_error("_general_", "The order of strings has changed.")
add_info("_general_", f"{len(original_keys_present_in_pending)} out of {len(original)} strings ({len(original_keys_present_in_pending) / len(original) * 100:.2f}%) have been translated.")

# count words in original and pending
original_word_count = 0
for key in original.keys():
	original_word_count += len(original[key].split())
pending_word_count = 0
for key in pending.keys():
	pending_word_count += len(pending[key].split())
add_info("_general_", f"Original has {original_word_count} words, pending has {pending_word_count} words.")

# check Google Translate results
for key in gt_same_meaning:
	if key in gt_identical:
		add_info(key, "This translation is identical to Google Translate.")
	elif key in gt_reversible:
		add_good_sign(key, "Reversing the translation yields the original string.")
	elif key in gt_reversible_artifacts:
		add_good_sign(key, "Reversing the translation yields the original string (plus Google Translate artifacts).")
num_gt_identical = len(gt_identical)
gt_identical_message = f"{num_gt_identical} out of {len(pending)} translations ({num_gt_identical / len(pending) * 100:.2f}%) are identical to Google Translate."
if num_gt_identical > len(pending) * 0.5:
	add_warning("_general_", gt_identical_message)
else:
	add_info("_general_", gt_identical_message)
add_info("_general_", f"{len(gt_same_meaning)} out of {len(pending)} translations ({len(gt_same_meaning) / len(pending) * 100:.2f}%) can be reversed with Google Translate.")

# check embeddings
low_distance_adjusted = low_distance_any - gt_same_meaning
for key in low_distance_adjusted:
	add_good_sign(key, get_low_distance_message(key))
add_info("_general_", f"{len(low_distance_adjusted)} out of {len(pending)} translations ({len(low_distance_adjusted) / len(pending) * 100:.2f}%) have a low embedding distance.")

# check extracted Minecraft names
for key in pending.keys():
	if key not in mcnames.keys():
		continue
	for name in mcnames[key]:
		translation = name["translation"]
		original_singular = name["original_singular"]
		translation_key = name["translation_key"]
		official_translation = name["official_translation"]
		if translation.lower() not in pending[key].lower():
			# if the translation isn't actually in pending, just add an info with the official translation
			add_info(key, f"Minecraft translates \"{original_singular}\" ({translation_key}) as \"{official_translation}\".")
		elif translation.lower() == official_translation.lower():
			add_good_sign(key, f"Minecraft translates \"{original_singular}\" ({translation_key}) as \"{official_translation}\", which is consistent with this translation.")
		else:
			add_warning(key, f"Possible inconsistency: Minecraft translates \"{original_singular}\" ({translation_key}) as \"{official_translation}\", but this translation says \"{translation}\" instead.")

# check for miscapitalized names
for name in wiki_data.keys():
	pattern = re.compile(name, re.IGNORECASE)
	for key in pending.keys():
		for match in re.finditer(pattern, pending[key]):
			# ignore .commands
			if match.start() > 0 and pending[key][match.start() - 1] == ".":
				continue
			# ignore .help commands
			if match.start() > 6 and pending[key][match.start() - 6:match.start()] == ".help ":
				continue
			# ignore correctly capitalized names
			if match.group() == name:
				continue
			add_error(key, f"Miscapitalized feature name: {match.group()} (should be {name})")

# compare formatting codes
for key in pending.keys():
	original_codes = re.findall(r"§[0-9a-fk-or]|%[sdf]", original.get(key, ""))
	pending_codes = re.findall(r"§[0-9a-fk-or]|%[sdf]", pending[key])
	if original_codes != pending_codes:
		add_warning(key, f"Formatting codes have changed: {''.join(original_codes)} -> {''.join(pending_codes)}")

# compare line breaks
for key in pending.keys():
	original_lines = re.findall(r"\n", original.get(key, ""))
	pending_lines = re.findall(r"\n", pending[key])
	if original_lines != pending_lines:
		add_warning(key, "Line breaks have changed.")

# check for deleted/changed names
for key in pending.keys():
	original_names = set(namefinder.get_names(original.get(key, "")))
	pending_names = set(namefinder.get_names(pending[key]))
	missing_names = original_names - pending_names
	for name in missing_names:
		add_warning(key, f"Name \"{name}\" is present in the original but not in the translation.")

# check for untranslated colors
color_pattern = re.compile(r"§[0-9a-fk-or](black|dark blue|dark green|dark aqua|dark red|dark purple|gold|gray|dark gray|blue|green|aqua|red|light purple|yellow|white|orange)§r")
for key in pending.keys():
	# check if original has any colors
	if color_pattern.search(original.get(key, "")) is None:
		continue
	# check if pending has any colors
	matches = color_pattern.finditer(pending[key])
	for match in matches:
		add_error(key, f"The color \"{match.group(1)}\" was not translated.")

# add info about the number of errors and warnings
error_count = 0
warning_count = 0
no_issues_count = 0
for key in evals.keys():
	if "errors" in evals[key]:
		error_count += len(evals[key]["errors"])
	if "warnings" in evals[key]:
		warning_count += len(evals[key]["warnings"])
	if "errors" not in evals[key] and "warnings" not in evals[key] and key in pending:
		no_issues_count += 1
add_info("_general_", f"{error_count} errors and {warning_count} warnings were found in total.")
add_info("_general_", f"{no_issues_count} out of {len(pending)} strings ({no_issues_count / len(pending) * 100:.2f}%) have no issues.")

# save the results
if not os.path.exists('cache'):
	os.makedirs('cache')
with open('cache/evals.json', 'w', encoding='utf-8') as f:
	json.dump(evals, f, indent=2)
