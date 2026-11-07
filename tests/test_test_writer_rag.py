
from agents.test_writer import generate_tests


corrected_code = """
def find_max(numbers):
    if not numbers:
        raise ValueError("Input list cannot be empty")

    max_value = numbers[0]

    for num in numbers[1:]:
        if num > max_value:
            max_value = num

    return max_value
"""


result = generate_tests(corrected_code)

print("\n========== TEST-WRITER RAG TEST ==========\n")
print(result)
