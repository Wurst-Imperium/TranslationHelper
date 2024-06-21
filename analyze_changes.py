"""
Experimanetal script that analyzes changes made to existing translations, rather than analyzing newly added translations. Saves its output as table2.html to not conflict with make_table.py.
"""
import requests
import json
import os
import sys
from github import Github
from urllib.parse import urlparse
from markdown2 import markdown


def get_pr_info(pr_url):
	parsed_url = urlparse(pr_url)
	path_parts = parsed_url.path.strip("/").split("/")
	owner, repo = path_parts[0], path_parts[1]
	pr_number = int(path_parts[3])
	return owner, repo, pr_number


def get_json_files(pr):
	json_file = None
	for file in pr.get_files():
		if file.filename.endswith(".json"):
			json_file = file.filename
			break
	if json_file:
		en_us_file = json_file.rsplit("/", 1)[0] + "/en_us.json"
		return json_file, en_us_file
	return None, None


def download_file(url, token):
	headers = {"Authorization": f"token {token}"}
	response = requests.get(url, headers=headers)
	response.raise_for_status()
	return response.text


def parse_json_as_strings(json_content):
	try:
		data = json.loads(json_content)
		if not isinstance(data, dict):
			raise ValueError("JSON content is not a simple key-value mapping")
		return {str(k): str(v) for k, v in data.items() if isinstance(v, (str, int, float, bool))}
	except json.JSONDecodeError as e:
		print(f"Error parsing JSON: {e}")
		print("JSON content:")
		print(json_content)
		raise


def compare_json_files(base_json, pr_json, en_us_json):
	differences = {}
	keys = sorted(set(base_json.keys()) | set(pr_json.keys()) | set(en_us_json.keys()))
	for key in keys:
		base_value = base_json.get(key)
		pr_value = pr_json.get(key)
		en_value = en_us_json.get(key)
		if base_value != pr_value:
			differences[key] = (base_value, pr_value, en_value)
	return differences


def explain_difference(
	key: str, base_value: str, pr_value: str, en_value: str, openai_api_key: str
) -> str:
	if base_value is None and pr_value is not None:
		return "Added"
	elif base_value is not None and pr_value is None:
		return "Removed"
	elif base_value == en_value:
		return "Same as English"
	elif base_value == pr_value:
		return "No change"

	prompt = f"""
	This is a pending translation for a Minecraft mod.
	Key: {key}
	Original English: {en_value}
	Original translation: {base_value}
	Pending translation: {pr_value}

	Please explain the change and critically analyze whether or not the pending translation actually improves anything over the original. Keep your response concise.
	"""

	headers = {
		"Authorization": f"Bearer {openai_api_key}",
		"Content-Type": "application/json",
	}
	data = {
		"model": "gpt-4o-2024-05-13",
		"messages": [{"role": "user", "content": prompt}],
	}

	try:
		response = requests.post(
			"https://api.openai.com/v1/chat/completions",
			headers=headers,
			json=data,
		)
		response.raise_for_status()
		explanation = response.json()["choices"][0]["message"]["content"].strip()
		return explanation
	except requests.exceptions.RequestException as e:
		return f"Error calling OpenAI API for {key}: {str(e)}, response: {e.response.text if e.response else None}"


def create_html_table(differences, openai_api_key):
	html = """
	<style>
	body {font-family: Arial, sans-serif;font-size: 14px;}
	table {border-collapse: collapse;width: 100%;margin-bottom: 20px;}
	thead {position: sticky;top: -1px;}
	th, td {text-align: left;padding: 8px;border: 1px solid #ddd;}
	th {background-color: #f2f2f2;color: #333;}
	</style>
	<table border="1">
		<colgroup>
			<col><col><col><col><col style="width: 25%">
		</colgroup>
		<tr style="text-align: center;">
			<th>Key</th>
			<th>English</th>
			<th>Original</th>
			<th>Pending</th>
			<th>Explanation</th>
		</tr>
	"""

	for key, (base_value, pr_value, en_value) in differences.items():
		explanation = markdown(
			explain_difference(key, base_value, pr_value, en_value, openai_api_key),
			extras=[
				"fenced-code-blocks",
				"tables",
				"code-friendly",
				"cuddled-lists",
			],
		)
		html += f"""
		<tr>
			<td>{key}</td>
			<td>{en_value if en_value is not None else ""}</td>
			<td>{base_value if base_value is not None else ""}</td>
			<td>{pr_value if pr_value is not None else ""}</td>
			<td>{explanation}</td>
		</tr>
		"""

	html += "</table>"
	return html


def main(pr_url):
	github_token = os.environ.get("GITHUB_TOKEN")
	openai_api_key = os.environ.get("OPENAI_API_KEY")
	if not github_token:
		raise ValueError("Please set the GITHUB_TOKEN environment variable")
	if not openai_api_key:
		raise ValueError("Please set the OPENAI_API_KEY environment variable")

	owner, repo_name, pr_number = get_pr_info(pr_url)

	g = Github(github_token)
	repo = g.get_repo(f"{owner}/{repo_name}")
	pr = repo.get_pull(pr_number)

	json_file, en_us_file = get_json_files(pr)

	if not json_file:
		print("No JSON file found in the Pull Request")
		return

	base_file_url = (
		f"https://raw.githubusercontent.com/{owner}/{repo_name}/{pr.base.sha}/{json_file}"
	)
	pr_file_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{pr.head.sha}/{json_file}"
	en_us_file_url = (
		f"https://raw.githubusercontent.com/{owner}/{repo_name}/{pr.base.sha}/{en_us_file}"
	)

	try:
		base_content = download_file(base_file_url, github_token)
		pr_content = download_file(pr_file_url, github_token)
		en_us_content = download_file(en_us_file_url, github_token)

		base_json = parse_json_as_strings(base_content)
		pr_json = parse_json_as_strings(pr_content)
		en_us_json = parse_json_as_strings(en_us_content)

		differences = compare_json_files(base_json, pr_json, en_us_json)

		if not differences:
			print("No differences found in the JSON files.")
		else:
			html_table = create_html_table(differences, openai_api_key)
			with open("table2.html", "w", encoding="utf-8") as f:
				f.write(html_table)
			print("Table has been saved to table2.html")

	except requests.exceptions.HTTPError as e:
		print(f"HTTP Error occurred: {e}")
		print(f"Base file URL: {base_file_url}")
		print(f"PR file URL: {pr_file_url}")
		print(f"English file URL: {en_us_file_url}")
	except Exception as e:
		print(f"An error occurred: {e}")


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python analyze_changes.py <GitHub PR URL>")
		sys.exit(1)
	main(sys.argv[1])
