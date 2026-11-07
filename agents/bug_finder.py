
import ast

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm import llm
from rag.vector_store import retrieve_guidelines


BUG_FINDER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an experienced software developer and debugging expert.

Your task is to identify actual bugs and potential runtime
problems in the submitted code.

Use the retrieved coding guidelines as supporting reference
material when analysing the code.

IMPORTANT RULES:

1. Focus on logical errors, runtime errors and edge cases.
2. Do not report style or formatting issues.
3. Do not report syntax or indentation errors.
4. Do not invent bugs that are not present.
5. Check boundary conditions and unusual inputs.
6. Check whether input validation is necessary.
7. Identify incorrect conditions, calculations and algorithms.
8. Identify unsafe or incorrect exception handling.
9. Distinguish confirmed bugs from potential risks.
10. Do not claim a recommendation is mandatory unless
    the retrieved guidelines explicitly say so.
11. If no bugs are found, clearly state that.
12. Explain findings in beginner-friendly language.

Organize your response into:

1. Bugs Identified
2. Explanation of Each Bug
3. Possible Consequences
4. Suggested Corrections
5. Overall Assessment

For every identified bug, mention the relevant code
section and explain why it is problematic.
        """
    ),
    (
        "human",
        """
Programming Language: {language}

RETRIEVED CODING GUIDELINES:
{guidelines}

CODE TO ANALYSE:
```{language}
{code}
```

Analyse the code and identify actual bugs or potential
runtime problems.
        """
    )
])


bug_finder_chain = BUG_FINDER_PROMPT | llm | StrOutputParser()


def find_bugs(code, language="Python"):

    # Check Python syntax before sending code to the LLM.
    if language == "Python":
        try:
            ast.parse(code)
        except SyntaxError as error:
            return (
                "Python Syntax Error:\n"
                f"Line {error.lineno}: {error.msg}\n"
                "Please correct the syntax before requesting "
                "bug analysis."
            )

    # Retrieve relevant coding guidelines.
    guidelines_text = "No additional coding guidelines retrieved."

    if language == "Python":
        try:
            documents = retrieve_guidelines(
                f"Python debugging, logical errors, "
                f"runtime errors, edge cases, input validation, "
                f"exception handling and performance:\n{code}",
                k=3
            )

            if documents:
                guidelines_text = "\n\n".join(
                    document.page_content
                    for document in documents
                )

        except Exception as error:
            print(f"Guideline retrieval warning: {error}")

    # Run the Bug-Finder LLM chain.
    result = bug_finder_chain.invoke({
        "code": code,
        "language": language,
        "guidelines": guidelines_text
    })

    return result
