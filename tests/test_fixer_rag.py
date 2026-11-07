
from agents.fixer import fix_code

original_code = """
def find_max(numbers):
    maximum = 0

    for num in numbers:
        if num < maximum:
            maximum = num

    return maximum


print(find_max([-10, -20, -5]))
"""


bug_report = """
1. Wrong comparison operator: num < maximum
   should be num > maximum.

2. Incorrect initialization: maximum = 0
   fails when all numbers are negative.

3. Empty-list handling is not defined.
"""

style_report = """
1. Use descriptive variable names where appropriate.
2. Consider adding a docstring.
3. Keep the function readable and maintainable.
"""


result = fix_code(
    original_code,
    "Python",
    bug_report,
    style_report
)

print("\n========== FIXER RAG TEST ==========\n")
print(result)
