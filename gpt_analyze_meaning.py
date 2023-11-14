"""
Shows the reverse-translated strings to ChatGPT and asks it if the meaning is the same as the original. Obviously error-prone, but it's pretty good at detecting strings that are completely different and separating them from the strings that are mostly fine.
"""
import json
import os
import time
import re
import openai_cost
import concurrent.futures
from tqdm import tqdm
from langfiles import original
from google_translate import reversed
import requests

model = "gpt-3.5-turbo-0613"
# model = "gpt-4-0613"
seed = 1337
MAX_RETRIES = 3
MAX_WORKERS = 20
TIMEOUT = 90

analyze_schema = {
	"name": "analyze",
	"description": "Analyze a variation of a string.",
	"parameters": {
		"type": "object",
		"properties": {
			"differences": {
				"type": "array",
				"description": "List the differences you see between the original and the variation.",
				"items": {
					"type": "object",
					"properties": {
						"difference": {
							"type": "string",
							"description": "Briefly describe the difference."
						},
						"impact": {
							"type": "string",
							"description": "How much does this difference change the meaning of the text?",
							"enum": ["None", "Low", "Medium", "High"]
						}
					},
					"required": ["difference", "impact"]
				}
			},
			"meaning": {
				"type": "string",
				"description": "Does the variation have the same meaning as the original text?",
				"enum": ["Same", "Different", "Unsure"]
			}
		},
		"required": ["meaning"]
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

def analyze_meaning():
	global meaning_analysis
	meaning_analysis = {}
	usages = []
	if not os.path.exists('cache/chatgpt'):
		os.makedirs('cache/chatgpt')

	# prepare the chats
	chats = {}
	print("Preparing chats...")
	for key in reversed.keys():
		if key not in original:
			continue
		# surround all § codes with square brackets to improve tokenization
		original_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", original[key])
		reversed_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", reversed[key])
		# skip identical strings, which obviously have the same meaning
		if original_value == reversed_value:
			continue
		user_message = f"Original:\n```\n{original_value}\n```\n\nVariation:\n```\n{reversed_value}\n```"
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
						meaning_analysis[key] = json.loads(result["choices"][0]["message"]["function_call"]["arguments"])
						with open("cache/chatgpt/meaning_analysis.json", "w", encoding='utf-8') as f:
							json.dump(meaning_analysis, f, indent=2)
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
						tqdm.write(f"Request for {key} failed after {MAX_RETRIES} retries: {e}")

		pbar.close()
	openai_cost.print_usage(usages, model)

cost_estimate = openai_cost.estimate(model, 162, 104, len(reversed))
if __name__ == "__main__":
	# ask user to confirm
	confirm = input(f"Analyzing {len(reversed)} strings with {model} will cost approximately ${cost_estimate}. Continue? (Y/n) ")
	if confirm.lower() != "n":
		analyze_meaning()
else:
	# check if meaning_analysis.json exists
	if os.path.isfile('cache/chatgpt/meaning_analysis.json'):
		with open('cache/chatgpt/meaning_analysis.json', encoding='utf-8') as f:
			meaning_analysis = json.load(f)
	else:
		# ask user to confirm
		confirm = input(f"No meaning analysis found. Analyzing {len(reversed)} strings with {model} will cost approximately ${cost_estimate}. Continue? (Y/n) ")
		if confirm.lower() != "n":
			analyze_meaning()
