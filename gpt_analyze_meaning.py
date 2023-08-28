"""
Shows the reverse-translated strings to ChatGPT and asks it if the meaning is the same as the original. Obviously error-prone, but it's pretty good at detecting strings that are completely different and separating them from the strings that are mostly fine.
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
from langfiles import original
from google_translate import reversed

model = "gpt-3.5-turbo-0613"
# model = "gpt-4-0613"

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

def request_completion(args):
	key, original_value, reversed_value = args
	user_message = f"Original:\n```\n{original_value}\n```\n\nVariation:\n```\n{reversed_value}\n```"
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

def analyze_meaning():
	global meaning_analysis
	meaning_analysis = {}
	usages = []
	if not os.path.exists('cache/chatgpt'):
		os.makedirs('cache/chatgpt')

	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		print("Requesting completions...")
		for key in tqdm(reversed.keys()):
			# surround all § codes with square brackets to improve tokenization
			original_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", original[key])
			reversed_value = re.sub(r'§.', lambda m: f"[{m.group(0)}]", reversed[key])
			# skip identical strings, which obviously have the same meaning
			if original_value == reversed_value:
				continue
			args = (key, original_value, reversed_value)
			futures.append(executor.submit(request_completion, args))
			time.sleep(0.1)

		print("Waiting for responses...")
		for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
			key, response = future.result()
			try:
				usages.append(response["usage"])
				args = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
				meaning_analysis[key] = args
				with open("cache/chatgpt/meaning_analysis.json", "w", encoding='utf-8') as f:
					json.dump(meaning_analysis, f, indent=2)
			except Exception as e:
				print(f"Got exception for key {key}: {e}\nTraceback: {traceback.format_exc()}\nResponse: {response}")

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
