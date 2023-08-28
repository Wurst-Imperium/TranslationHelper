"""
Downloads the pending translation from a pull request.
"""
import os
import requests
import sys

def download_pending(url):
	# Build the file list URL from the pull request URL
	repo = '/'.join(url.split('/')[3:5])
	pr_number = url.split('/')[-1]
	pr_files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"

	# Set up the headers for the API request
	headers = {
		"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
		"X-GitHub-Api-Version": "2022-11-28"
	}

	# Send GET request to get the file list
	print(f"Downloading file list from {pr_files_url}...")
	response = requests.get(pr_files_url, headers=headers)
	response.raise_for_status()

	# Get the json response content
	files = response.json()

	# Find the first JSON file that was added or modified
	for file in files:
		if (file['status'] == 'added' or file['status'] == 'modified') and file['filename'].endswith('.json'):
			# Download the file
			json_file_content = requests.get(file['raw_url'], headers=headers).text

			# Get the language code from the filename and save it
			langcode = file['filename'].split('/')[-1][:-5].lower()
			with open(f"pending_lang.txt", 'w', encoding='utf-8') as f:
				f.write(langcode)

			# Write the file content to 'pending.json'
			with open('pending.json', 'w', encoding='utf-8') as f:
				f.write(json_file_content)
			print(f"File {file['filename'].split('/')[-1]} has been saved as pending.json")
			return

	print("No JSON file was found in the PR")

if __name__ == "__main__":
	if len(sys.argv) == 2:
		download_pending(sys.argv[1])
	else:
		url = input("Enter the URL of the pull request: ")
		download_pending(url)
