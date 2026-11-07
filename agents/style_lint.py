
import ast

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm import llm
from rag.vector_store import retrieve_guidelines


STYLE_LINT_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an experienced Python code reviewer.

Your task is to review code for style, readability,
maintainability, and Python best practices.

Use the retrieved coding guidelines as supporting
reference material.

IMPORTANT RULES:

1. Focus on actual style and maintainability issues.
2. Do not report syntax or indentation errors.
3. Do not invent problems that are not present.
4. Distinguish actual issues from optional improvements.
5. Do not describe optional type hints or docstrings
   as mandatory requirements.
6. Do not claim a recommendation is mandatory unless
   the retrieved guidelines explicitly say so.
7. Avoid repeating the same observation.
8. If the code is already good, say so clearly.
9. Keep the review understandable for students.

Organize your response into:

1. Naming Conventions
2. Readability and Formatting
3. Code Organization
4. Maintainability
5. Recommended Improvements
6. Overall Assessment

If a category has no issues, mention that briefly.
        """
    ),
    (
        "human",
        """
Programming Language: {language}

RETRIEVED CODING GUIDELINES:
{guidelines}

CODE TO REVIEW:
```{language}
{code}
```

Review the submitted code using the instructions above.
        """
    )
])


style_lint_chain = STYLE_LINT_PROMPT | llm | StrOutputParser()


def review_style(code, language="Python"):

    # Check Python syntax before sending code to the LLM.
    if language == "Python":
        try:
            ast.parse(code)
        except SyntaxError as error:
            return (
                "Python Syntax Error:\n"
                f"Line {error.lineno}: {error.msg}\n"
                "Please correct the syntax before requesting "
                "a style review."
            )

    # Retrieve relevant coding guidelines for Python.
    guidelines_text = "No additional coding guidelines retrieved."

    if language == "Python":
        try:
            documents = retrieve_guidelines(
                f"Python coding style, naming conventions, "
                f"readability and maintainability:\n{code}",
                k=3
            )

            if documents:
                guidelines_text = "\n\n".join(
                    document.page_content
                    for document in documents
                )

        except Exception as error:
            print(f"Guideline retrieval warning: {error}")

    # Run the Style/Lint LLM chain.
    result = style_lint_chain.invoke({
        "code": code,
        "language": language,
        "guidelines": guidelines_text
    })

    return result
