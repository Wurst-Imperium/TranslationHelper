"""
Shows the original and pending strings to ChatGPT and asks it to extract the names of Minecraft things, as well as what those things were translated to. This data is then cleaned up and checked against Minecraft's official translations to detect inconsistencies. ChatGPT misses a few names, but it works pretty well overall.
"""
import json
import os
import time
import re
import traceback
import openai
import openai_cost
import concurrent.futures
from tqdm import tqdm
from langfiles import original, pending, langcode
import i18n

model = "gpt-3.5-turbo-0613"
# model = "gpt-4-0613"

analyze_schema = {
	"name": "analyze",
	"description": "Extract names of Minecraft items, blocks, mobs, etc. from the given string and its translation. Keep in mind that many new things have been added to Minecraft since your knowledge cutoff date. If you see something that looks like a Minecraft thing but you don't recognize it, include it anyway.",
	"parameters": {
		"type": "object",
		"properties": {
			"names": {
				"type": "array",
				"description": "List all the Minecraft things you see in the string.",
				"items": {
					"type": "object",
					"properties": {
						"original": {
							"type": "string",
							"description": "What the Minecraft thing is called in the original string."
						},
						"translation": {
							"type": "string",
							"description": "What the Minecraft thing is called in the translation string."
						},
						"original_singular": {
							"type": "string",
							"description": "Convert the original name to singular form. Return the original name if it's already singular."
						}
					},
					"required": ["original", "translation", "original_singular"]
				}
			}
		},
		"required": ["names"]
	}
}

def request_completion(args):
	key, original_value, pending_value = args
	user_message = f"Original:\n```\n{original_value}\n```\n\nTranslation:\n```\n{pending_value}\n```"
	messages = [{"role": "user", "content": user_message}]
	response = openai.ChatCompletion.create(
		model=model,
		temperature=0,
		messages=messages,
		functions=[analyze_schema],
		function_call={"name": "analyze"},
		timeout=120
	)
	# print(messages, response)
	return key, response

def analyze_mcnames():
	global mcnames
	usages = []
	if not os.path.exists('cache/chatgpt'):
		os.makedirs('cache/chatgpt')

	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		print("Requesting completions...")
		for key in tqdm(pending.keys()):
			if key in mcnames:
				continue
			# surround all § codes with square brackets to improve tokenization
			original_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", original[key])
			pending_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", pending[key])
			# skip untranslated strings
			if original_value == pending_value:
				continue
			args = (key, original_value, pending_value)
			futures.append(executor.submit(request_completion, args))
			time.sleep(0.1)

		print("Waiting for responses...")
		for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
			key, response = future.result()
			try:
				usages.append(response["usage"])
				args = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
				mcnames[key] = args["names"]
				with open("cache/chatgpt/mcnames.json", "w", encoding='utf-8') as f:
					json.dump(mcnames, f, indent=2)
			except Exception as e:
				print(f"Got exception for key {key}: {e}\nTraceback: {traceback.format_exc()}\nResponse: {response}")

	openai_cost.print_usage(usages, model)

cost_estimate = openai_cost.estimate(model, 201, 85, len(pending))
if __name__ == "__main__":
	# ask user to confirm
	confirm = input(f"Analyzing {len(pending)} strings with {model} will cost approximately ${cost_estimate}. Continue? (Y/n) ")
	if confirm.lower() != "n":
		mcnames = {}
		analyze_mcnames()
else:
	# check if mcnames.json exists
	if os.path.isfile('cache/chatgpt/mcnames.json'):
		with open('cache/chatgpt/mcnames.json', encoding='utf-8') as f:
			mcnames = json.load(f)
	else:
		# ask user to confirm
		confirm = input(f"No mcnames analysis found. Analyzing {len(pending)} strings with {model} will cost approximately ${cost_estimate}. Continue? (Y/n) ")
		if confirm.lower() != "n":
			mcnames = {}
			analyze_mcnames()

# clean up the data
cleaned_mcnames = {}
for key in mcnames.keys():
	for name in mcnames[key]:
		# remove mcnames that don't contain "original" or "translation"
		if "original" not in name or "translation" not in name:
			continue
		# remove mcnames that aren't actually present in original
		elif name["original"].lower() not in original[key].lower():
			continue
		# remove mcnames that don't actually exist in Minecraft
		trkey = i18n.reverse_lookup(name.get("original_singular", name["original"]), fallback=False)
		if trkey is False:
			continue
		# remove mcnames with no official translation
		official_translation = i18n.translate(trkey, langcode, False)
		if official_translation is False:
			continue
		# fix mcnames that don't contain "original_singular"
		if "original_singular" not in name:
			name["original_singular"] = name["original"]
		# add trkey and official_translation
		name["translation_key"] = trkey
		name["official_translation"] = official_translation
		# add to cleaned_mcnames
		if key not in cleaned_mcnames:
			cleaned_mcnames[key] = []
		cleaned_mcnames[key].append(name)
mcnames = cleaned_mcnames
del cleaned_mcnames
