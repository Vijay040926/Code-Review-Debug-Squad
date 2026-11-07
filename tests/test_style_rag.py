
from agents.style_lint import review_style


sample_code = """
def calc(a,b):
    x=a+b
    y=a-b
    print(x)
    print(y)

calc(10,5)
"""


result = review_style(sample_code, "Python")

print("\n========== STYLE/LINT RAG TEST ==========\n")
print(result)
