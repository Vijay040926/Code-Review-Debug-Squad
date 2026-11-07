
from agents.bug_finder import find_bugs


sample_code = """
def find_max(numbers):
    maximum = 0

    for num in numbers:
        if num < maximum:
            maximum = num

    return maximum


print(find_max([-10, -20, -5]))
"""


result = find_bugs(sample_code, "Python")

print("\n========== BUG-FINDER RAG TEST ==========\n")
print(result)
