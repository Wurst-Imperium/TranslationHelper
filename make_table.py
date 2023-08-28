"""
Creates the table.html file and requests all the necessary data from the other scripts.
"""
import re
import pandas as pd
import html
from langfiles import original, pending, langcode_short
from google_translate import forward, reversed
from evaluate import evals
from gpt_analyze_meaning import meaning_analysis
from gpt_extract_mcnames import mcnames
import namefinder

def format_translation(translations, key):
	translation = translations.get(key, "(no data)")
	translation = html.escape(translation).replace('\n', '<br>')
	# highlight formatting codes
	translation = re.sub(r'§[0-9a-fk-or]|%[sdf]', lambda m: f"<mark class='code'>{m.group(0)}</mark>", translation)
	# highlight names
	translation = namefinder.mark_names(translation)
	return translation

def format_evaluation(key):
	evaluation = evals.get(key, {})
	html = ""
	for error in evaluation.get('errors', []):
		html += f"<span class='error'><b>Error:</b>&nbsp;{error}</span><br>"
	for warning in evaluation.get('warnings', []):
		html += f"<span class='warning'><b>Warning:</b>&nbsp;{warning}</span><br>"
	for good_sign in evaluation.get('good_signs', []):
		html += f"<span class='good'><b>Good sign:</b>&nbsp;{good_sign}</span><br>"
	for info in evaluation.get('info', []):
		html += f"<span class='info'><b>Info:</b>&nbsp;{info}</span><br>"
	return html[:-4] if html.endswith('<br>') else html

def has_major_issues(classification):
	return classification['language'] == 'Still in English' or classification['language'] == 'Other language' or classification['meaning'] == 'Different' or classification['grammar'] == 'Poor' or classification['context'] == 'Incorrect' or classification['formatting'] == 'Incorrect'

# create table
df = pd.DataFrame(columns=["Key", "Evaluation", "Pending", "Reverse-Translated", "Original"])

# add rows to table
for key in original.keys():
	evaluation_value = format_evaluation(key)
	original_value = format_translation(original, key)
	pending_value = format_translation(pending, key)

	# highlight minecraft names, starting with the longest name to avoid replacing substrings
	for name in sorted(mcnames.get(key, []), key=lambda name: len(name["translation"]), reverse=True):
		if name["translation"] not in pending_value:
			continue
		original_value = original_value.replace(name["original"], f"<mark class='mcname' title='{name['official_translation']}'>{name['original']}</mark>")
		if name["translation"].lower() != name["official_translation"].lower():
			pending_value = pending_value.replace(name["translation"], f"<mark class='error no-expand' title='\"{name['original_singular']}\", which Minecraft translates as \"{name['official_translation']}\" ({name['translation_key']}).'>{name['translation']}</mark>")
		else:
			pending_value = pending_value.replace(name["translation"], f"<mark class='mcname' title='\"{name['original_singular']}\" ({name['translation_key']})'>{name['translation']}</mark>")

	# format reverse translation based on meaning analysis
	reversed_value = format_translation(reversed, key)
	if original.get(key, None) == reversed.get(key, None):
		reversed_value = f"<span class='good' title='Reversing the translation yields the original string.'>{reversed_value}</span>"
	elif pending.get(key, None) == forward.get(key, None):
		reversed_value = f"<span class='good' title='Meaning is probably the same because the translation is identical to Google Translate.'>{reversed_value}</span>"
	elif meaning_analysis.get(key, {}).get('meaning', None) == 'Same':
		reversed_value = f"<span class='good' title='ChatGPT thinks the reverse translation has the same meaning as the original.'>{reversed_value}</span>"
	elif meaning_analysis.get(key, {}).get('meaning', None) == 'Different':
		differences = [diff for diff in meaning_analysis[key]['differences'] if diff['impact'] != 'None']
		for diff in differences:
			reversed_value = reversed_value.replace(diff['difference'], f"<span class='error no-expand' title='ChatGPT thinks this part changes the meaning ({diff['impact'].lower()} impact).'>{diff['difference']}</span>")

	row = {"Key": html.escape(key), "Evaluation": evaluation_value, "Pending": pending_value, "Reverse-Translated": reversed_value, "Original": original_value}
	df = pd.concat([df, pd.DataFrame(row, index=[0])])

# convert dataframe to html table
html_table = df.to_html(index=False, justify='center', escape=False)
html_table += f"<div class='general-evaluation'>{format_evaluation('_general_')}</div>"
html_table += "<div class='progress-bar'></div>"
html_table += f"<meta lang='{langcode_short}'>"

css = """
<style>
table {
	border-collapse: collapse;
	width: 100%;
	font-family: Arial, sans-serif;
	font-size: 14px;
	margin-bottom: 20px;
}
thead {
	position: sticky;
	top: -1px;
}
th, td {
	text-align: left;
	padding: 8px;
	border: 1px solid #ddd;
}
th {
	background-color: #f2f2f2;
	color: #333;
}
tr:nth-child(even) {
	background-color: #f2f2f2;
}
tr:hover {
	background-color: #ddd;
}
tr.selected {
	border: 2px solid #f00;
}
.general-evaluation {
	margin-top: 20px;
}
.good {
	background-color: #d4f4d4;
}
tr:nth-child(even) td.good {
	background-color: #c1f1c1;
}
tr:hover td.good {
	background-color: #b1eeb1;
}
td.colored-cell span.error,
td.colored-cell span.warning,
td.colored-cell span.good {
	background-color: transparent;
}
.warning {
	background-color: #ffffdd;
}
tr:nth-child(even) td.warning {
	background-color: #ffffcc;
}
tr:hover td.warning {
	background-color: #ffffbb;
}
.error {
	background-color: #ffdddd;
}
.error.no-expand {
	background-color: #f88;
}
tr:nth-child(even) td.error {
	background-color: #ffcccc;
}
tr:hover td.error {
	background-color: #ffbbbb;
}
mark.name {
	background-color: #0ff;
}
mark.mcname {
	background-color: #8f8;
}
div.progress-bar {
	position: fixed;
	top: 0;
	left: 0;
	height: 2px;
	background-color: #f00;
	width: 0;
	transition: width 0.2s ease-in-out;
}
div.progress-bar.complete {
	background-color: #0f0;
}
.context-menu-item {
	position: absolute;
	background-color: #fff;
}
</style>
"""

js = """
<script>
let table = document.getElementsByTagName('table')[0];
let rows = table.rows;

for (let i = 1; i < rows.length; i++) {
	let row = rows[i];
	for (let j = 0; j < row.cells.length; j++) {
		let cell = row.cells[j];
		if (cell.querySelector('.error:not(.no-expand)') !== null) {
			cell.classList.add('error');
			cell.classList.add('colored-cell');
		} else if (cell.querySelector('.warning:not(.no-expand)') !== null) {
			cell.classList.add('warning');
			cell.classList.add('colored-cell');
		} else if (cell.querySelector('.good:not(.no-expand)') !== null) {
			cell.classList.add('good');
			cell.classList.add('colored-cell');
		}
	}
}

let selectedRow = parseInt(localStorage.getItem('selectedRow')) || 1;
rows[selectedRow].classList.add('selected');
console.log(`Selected row: ${selectedRow}`);

let progressBar = document.querySelector('.progress-bar');
function updateProgressBar() {
	let progress = (selectedRow / (rows.length - 1)) * 100;
	progressBar.style.width = `${progress}%`;
	if (selectedRow === rows.length - 1)
		progressBar.classList.add('complete');
	else
		progressBar.classList.remove('complete');
}
updateProgressBar();

function moveSelectionToRow(row) {
	rows[selectedRow].classList.remove('selected');
	selectedRow = row;
	rows[selectedRow].classList.add('selected');
	localStorage.setItem('selectedRow', selectedRow.toString());
	updateProgressBar();
	console.log(`Selected row: ${selectedRow}`);
}
document.addEventListener('keydown', (event) => {
	if (event.key === 'ArrowDown')
		moveSelectionToRow((selectedRow + 1) % rows.length);
	else if (event.key === 'ArrowUp')
		moveSelectionToRow((selectedRow - 1 + rows.length) % rows.length);
});

const lang = document.querySelector('meta[lang]').getAttribute('lang');

// Add context menu entries for Google Translate and DeepL
document.addEventListener('contextmenu', (event) => {
	const selectedText = window.getSelection().toString();
	if (selectedText !== '') {
		const encodedText = encodeURIComponent(selectedText);
		const googleurl = `https://translate.google.com/?op=translate&sl=${lang}&tl=en&text=${encodedText}`;
		const deepLurl = `https://www.deepl.com/translator#${lang}/en/${encodedText}`;
		const googleItem = document.createElement('a');
		googleItem.classList.add('context-menu-item');
		googleItem.href = googleurl;
		googleItem.target = '_blank';
		googleItem.innerText = 'View in Google Translate (G)';
		googleItem.style.top = `${event.pageY-40}px`;
		googleItem.style.left = `${event.pageX}px`;
		document.body.appendChild(googleItem);
		const deepLItem = document.createElement('a');
		deepLItem.classList.add('context-menu-item');
		deepLItem.href = deepLurl;
		deepLItem.target = '_blank';
		deepLItem.innerText = 'View in DeepL (D)';
		deepLItem.style.top = `${event.pageY-20}px`;
		deepLItem.style.left = `${event.pageX}px`;
		document.body.appendChild(deepLItem);
	}
});

// Remove the context menu entries when the menu is closed
document.addEventListener('click', () => {
	const menuItem = document.querySelectorAll('a.context-menu-item');
	menuItem.forEach((item) => {
		item.parentNode.removeChild(item);
	});
});

// Add keyboard shortcuts for the context menu entries
document.addEventListener('keydown', (event) => {
	const selectedText = window.getSelection().toString();
	if (selectedText !== '') {
		const encodedText = encodeURIComponent(selectedText);
		if (event.key === 'g') {
			const googleurl = `https://translate.google.com/?op=translate&sl=${lang}&tl=en&text=${encodedText}`;
			window.open(googleurl, '_blank');
		} else if (event.key === 'd') {
			const deepLurl = `https://www.deepl.com/translator#${lang}/en/${encodedText}`;
			window.open(deepLurl, '_blank');
		}
	}
});
</script>
"""

# save table to file
with open('table.html', 'w', encoding='utf-8') as f:
	f.write("<!DOCTYPE html>\n" + css + html_table + js)
