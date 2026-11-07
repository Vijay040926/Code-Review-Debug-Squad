from utils.llm import get_llm_response

response = get_llm_response(
    "Explain what a Python logical error is in two sentences."
)

print("\nLLM Response:")
print(response)