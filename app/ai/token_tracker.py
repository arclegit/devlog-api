# app/ai/token_tracker.py
import tiktoken
from app.config import AI_MODEL

def count_tokens(text: str, model: str = AI_MODEL) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def calculate_cost(prompt_tokens: int, completion_tokens: int, model: str = AI_MODEL) -> float:
    # Example cost calculation (adjust based on actual pricing)
    if "gpt-5" in model:
        prompt_cost = prompt_tokens * 0.00001
        completion_cost = completion_tokens * 0.00002
    else:
        prompt_cost = prompt_tokens * 0.000005
        completion_cost = completion_tokens * 0.00001
    return prompt_cost + completion_cost