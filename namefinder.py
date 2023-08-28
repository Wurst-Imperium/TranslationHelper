"""
Detects names of Wurst features as well as anything in names.txt.
This doesn't include Minecraft names. See gpt_extract_mcnames.py for that.
"""
import re
from wiki_data import wiki_data

names = []

# add feature names from wiki data
for name in wiki_data.keys():
	names.append(name)

# add special names from names.txt
with open('names.txt', 'r', encoding='utf-8') as f:
	for line in f:
		line = line.strip()
		if line.startswith('#'):
			continue
		names.append(line)

# generate a regular expression pattern that matches all the names in the list
pattern = re.compile('|'.join(map(re.escape, names)))

# highlight all names in text
def mark_names(text):
	return re.sub(pattern, lambda m: f"<mark class='name'>{m.group(0)}</mark>", text)

# get all names as strings
def get_names(text):
	return re.findall(pattern, text)

# get all names as match objects
def get_name_matches(text):
	return re.finditer(pattern, text)

# TODO: It might make sense to cache this, since the regex can be quite slow.
