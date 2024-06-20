"""
Shows the original and pending strings to ChatGPT and asks it to extract the names of Minecraft things, as well as what those things were translated to. This data is then cleaned up and checked against Minecraft's official translations to detect inconsistencies. ChatGPT misses a few names, but it works pretty well overall.
"""
import json
import os
import time
import re
import requests
import openai_cost
import concurrent.futures
from tqdm import tqdm
from langfiles import original, pending, langcode
import i18n

model = "gpt-3.5-turbo-0125"
# model = "gpt-4o-2024-05-13"
seed = 1337
MAX_RETRIES = 3
MAX_WORKERS = 20
TIMEOUT = 90

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

def request_completion(messages):
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
	}
	payload = {
		"model": model,
		"seed": seed,
		"messages": messages,
		"functions": [analyze_schema],
		"function_call": {"name": "analyze"},
	}
	response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=TIMEOUT)
	response.raise_for_status()
	return response.json()

def analyze_mcnames():
	global mcnames
	usages = []
	if not os.path.exists('cache/chatgpt'):
		os.makedirs('cache/chatgpt')

	# prepare the chats
	chats = {}
	print("Preparing chats...")
	for key in pending.keys():
		if key in mcnames or key not in original:
			continue
		# surround all § codes with square brackets to improve tokenization
		original_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", original[key])
		pending_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", pending[key])
		# skip untranslated strings
		if original_value == pending_value:
			continue
		user_message = f"Original:\n```\n{original_value}\n```\n\nTranslation:\n```\n{pending_value}\n```"
		messages = [{"role": "user", "content": user_message}]
		chats[key] = messages

	# initialize the progress bar and dict to keep track of retries
	pbar = tqdm(total=len(chats), desc="Requests", unit="request")
	retries = {key: 0 for key in chats.keys()}

	tqdm.write("Requesting completions...")
	with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
		future_to_key = {executor.submit(request_completion, data): key for key, data in chats.items()}

		while future_to_key:
			# wait for the next future to complete
			done, _ = concurrent.futures.wait(
				future_to_key.keys(),
				return_when=concurrent.futures.FIRST_COMPLETED
			)

			for future in done:
				key = future_to_key.pop(future)
				try:
					result = future.result()
					pbar.update(1)
					if "usage" in result:
						usages.append(result["usage"])
					if "choices" in result:
						mcnames[key] = json.loads(result["choices"][0]["message"]["function_call"]["arguments"])["names"]
						with open("cache/chatgpt/mcnames.json", "w", encoding='utf-8') as f:
							json.dump(mcnames, f, indent=2)
				except Exception as e:
					retries[key] += 1
					if retries[key] < MAX_RETRIES:
						# write the error message to the console
						tqdm.write(f"Retrying request for {key} ({retries[key]}/{MAX_RETRIES}) after error: {e}")
						time.sleep(retries[key]**3)
						# resubmit the task to the executor
						new_future = executor.submit(request_completion, chats[key])
						future_to_key[new_future] = key
					else:
						# write the error message to the console
						tqdm.write(f"Failed request for {key} after {MAX_RETRIES} retries: {e}")

		pbar.close()
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
		if "original" not in name or name["original"] is None or name["original"] == "":
			continue
		if "translation" not in name or name["translation"] is None or name["translation"] == "":
			continue
		# remove mcnames that aren't actually present in original
		if name["original"].lower() not in original[key].lower():
			continue
		# get original_singular, or fallback to original
		original_singular = name.get("original_singular", None)
		if original_singular is None or original_singular == "":
			original_singular = name["original"]
		# remove mcnames that don't actually exist in Minecraft
		trkey = i18n.reverse_lookup(original_singular, fallback=False)
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
