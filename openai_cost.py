"""
Utility script for calculating OpenAI API costs.
"""

# OpenAI pricing per 1M tokens
pricing = {
	"gpt-3.5-turbo-1106": {"prompt": 1, "completion": 2},
	"gpt-3.5-turbo-0125": {"prompt": 0.5, "completion": 1.5},
	"gpt-4-1106-preview": {"prompt": 10, "completion": 30},
	"gpt-4-0125-preview": {"prompt": 10, "completion": 30},
	"gpt-4-turbo-2024-04-09": {"prompt": 10, "completion": 30},
	"gpt-4o-2024-05-13": {"prompt": 5, "completion": 15},
}


def print_usage(usages, model, estimate_other_model=True):
	# get total usage
	total_prompt_tokens = 0
	total_completion_tokens = 0
	for usage in usages:
		total_prompt_tokens += usage["prompt_tokens"]
		total_completion_tokens += usage["completion_tokens"]
	total_tokens = total_prompt_tokens + total_completion_tokens
	print(f"Token usage: {total_tokens} ({total_prompt_tokens} prompt tokens, {total_completion_tokens} completion tokens)")

	cost = get_estimate_string(model, total_prompt_tokens, total_completion_tokens)
	print(f"Cost: {cost}")

	if estimate_other_model:
		if model.startswith("gpt-4"):
			cost_35t = get_estimate_string("gpt-3.5-turbo-0125", total_prompt_tokens, total_completion_tokens)
			print(f"Estimated GPT-3.5-Turbo cost: {cost_35t}")
		else:
			cost_4t = get_estimate_string("gpt-4-turbo-2024-04-09", total_prompt_tokens, total_completion_tokens)
			print(f"Estimated GPT-4-Turbo cost: {cost_4t}")
			cost_4o = get_estimate_string("gpt-4o-2024-05-13", total_prompt_tokens, total_completion_tokens)
			print(f"Estimated GPT-4o cost: {cost_4o}")


def get_estimate_string(model: str, prompt_tokens: int, completion_tokens: int):
	prompt_cost = pricing[model]["prompt"] * prompt_tokens / 1e6
	completion_cost = pricing[model]["completion"] * completion_tokens / 1e6
	total_cost = prompt_cost + completion_cost
	return f"${total_cost} (${prompt_cost} for prompt tokens, ${completion_cost} for completion tokens)"


def estimate(model: str, prompt_tokens: int, completion_tokens: int, iterations=1):
	prompt_cost = pricing[model]["prompt"] * prompt_tokens * iterations / 1e6
	completion_cost = pricing[model]["completion"] * completion_tokens * iterations / 1e6
	total_cost = prompt_cost + completion_cost
	return total_cost
