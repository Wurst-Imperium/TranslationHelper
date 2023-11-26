import os
import json
import requests
from tqdm import tqdm
from langfiles import original, pending
from google_translate import forward, reversed, forward_reverse
from dotenv import load_dotenv

load_dotenv()
embeddings = {}
TIMEOUT = 300

def create_embedding_batch(texts):
	tqdm.write(f"Requesting embeddings for {len(texts)} texts...")
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
	}
	payload = {
		"input": texts,
		"model": "text-embedding-ada-002"
	}
	response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload, timeout=TIMEOUT)
	response.raise_for_status()
	return response.json()["data"]

def create_all_embeddings():
	global embeddings

	# embed original texts
	texts = [text for text in original.values()]
	embs = create_embedding_batch(texts)
	for i, key in enumerate(original):
		embedding = embs[i]["embedding"]
		if key not in embeddings:
			embeddings[key] = {}
		embeddings[key]["original"] = embedding

	# embed pending texts
	texts = [text for text in pending.values()]
	embs = create_embedding_batch(texts)
	for i, key in enumerate(pending):
		embedding = embs[i]["embedding"]
		if key not in embeddings:
			embeddings[key] = {}
		embeddings[key]["pending"] = embedding

	# embed forward texts
	texts = [text for text in forward.values()]
	embs = create_embedding_batch(texts)
	for i, key in enumerate(forward):
		embedding = embs[i]["embedding"]
		if key not in embeddings:
			embeddings[key] = {}
		embeddings[key]["forward"] = embedding

	# embed reversed texts
	texts = [text for text in reversed.values()]
	embs = create_embedding_batch(texts)
	for i, key in enumerate(reversed):
		embedding = embs[i]["embedding"]
		if key not in embeddings:
			embeddings[key] = {}
		embeddings[key]["reversed"] = embedding

	# embed forward-reversed texts
	texts = [text for text in forward_reverse.values()]
	embs = create_embedding_batch(texts)
	for i, key in enumerate(forward_reverse):
		embedding = embs[i]["embedding"]
		if key not in embeddings:
			embeddings[key] = {}
		embeddings[key]["forward_reverse"] = embedding

# check if embeddings.json exists
if os.path.exists("cache/chatgpt/embeddings.json"):
	print("Loading embeddings from cache...")
	with open("cache/chatgpt/embeddings.json", "r", encoding="utf-8") as f:
		embeddings = json.load(f)
else:
	print("Creating embeddings...")
	create_all_embeddings()
	with open("cache/chatgpt/embeddings.json", "w", encoding="utf-8") as f:
		json.dump(embeddings, f, indent=2)

def get_distance(key, type1, type2):
	return sum((a - b) ** 2 for a, b in zip(embeddings[key][type1], embeddings[key][type2])) ** 0.5

source_threshold = 0.185
target_threshold = 0.197
source_vs_gt_threshold = -0.043

low_source_distance = {}
low_target_distance = {}
low_source_vs_gt_distance = {}
low_distance_any = set()

print("Calculating distances...")
for key in embeddings:
	if "original" not in embeddings[key] or "pending" not in embeddings[key]:
		continue

	source_distance = get_distance(key, "original", "reversed")
	target_distance = get_distance(key, "forward", "pending")
	source_gt_distance = get_distance(key, "original", "forward_reverse")
	source_vs_gt_distance = source_distance - source_gt_distance

	if source_distance <= source_threshold:
		low_source_distance[key] = source_distance
		low_distance_any.add(key)
	if target_distance <= target_threshold:
		low_target_distance[key] = target_distance
		low_distance_any.add(key)
	if source_vs_gt_distance <= source_vs_gt_threshold:
		low_source_vs_gt_distance[key] = source_vs_gt_distance
		low_distance_any.add(key)

def get_low_distance_message(key):
	low_distances = []
	if key in low_source_distance:
		low_distances.append(f"src={low_source_distance[key]:.3f}")
	if key in low_target_distance:
		low_distances.append(f"tgt={low_target_distance[key]:.3f}")
	if key in low_source_vs_gt_distance:
		low_distances.append(f"relsrc={low_source_vs_gt_distance[key]:.3f}")
	return f"Low embedding distance ({', '.join(low_distances)})."
