"""
Utility script for calculating OpenAI API costs.
"""

# OpenAI pricing per 1K tokens
pricing = {
	"gpt-3.5-turbo": {
		"prompt": 0.0015,
		"completion": 0.002
	},
	"gpt-3.5-turbo-0301": {
		"prompt": 0.0015,
		"completion": 0.002
	},
	"gpt-3.5-turbo-0613": {
		"prompt": 0.0015,
		"completion": 0.002
	},
	"gpt-3.5-turbo-16k": {
		"prompt": 0.003,
		"completion": 0.004
	},
	"gpt-3.5-turbo-16k-0613": {
		"prompt": 0.003,
		"completion": 0.004
	},
	"gpt-4": {
		"prompt": 0.03,
		"completion": 0.06
	},
	"gpt-4-0314": {
		"prompt": 0.03,
		"completion": 0.06
	},
	"gpt-4-0613": {
		"prompt": 0.03,
		"completion": 0.06
	},
	"gpt-4-32k": {
		"prompt": 0.06,
		"completion": 0.12
	},
	"gpt-4-32k-0314": {
		"prompt": 0.06,
		"completion": 0.12
	},
	"gpt-4-32k-0613": {
		"prompt": 0.06,
		"completion": 0.12
	}
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

	prompt_cost = pricing[model]["prompt"] * total_prompt_tokens / 1000
	completion_cost = pricing[model]["completion"] * total_completion_tokens / 1000
	total_cost = prompt_cost + completion_cost
	print(f"Cost: ${total_cost} (${prompt_cost} for prompt tokens, ${completion_cost} for completion tokens)")

	if estimate_other_model:
		if model.startswith("gpt-4"):
			prompt_cost = pricing["gpt-3.5-turbo"]["prompt"] * total_prompt_tokens / 1000
			completion_cost = pricing["gpt-3.5-turbo"]["completion"] * total_completion_tokens / 1000
			total_cost = prompt_cost + completion_cost
			print(f"Estimated GPT-3.5-Turbo cost: ${total_cost} (${prompt_cost} for prompt tokens, ${completion_cost} for completion tokens)")
		else:
			prompt_cost = pricing["gpt-4"]["prompt"] * total_prompt_tokens / 1000
			completion_cost = pricing["gpt-4"]["completion"] * total_completion_tokens / 1000
			total_cost = prompt_cost + completion_cost
			print(f"Estimated GPT-4 cost: ${total_cost} (${prompt_cost} for prompt tokens, ${completion_cost} for completion tokens)")

def estimate(model: str, prompt_tokens: int, completion_tokens: int, iterations=1):
	prompt_cost = pricing[model]["prompt"] * prompt_tokens * iterations / 1000
	completion_cost = pricing[model]["completion"] * completion_tokens * iterations / 1000
	total_cost = prompt_cost + completion_cost
	return total_cost
