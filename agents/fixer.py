
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm import llm
from rag.vector_store import retrieve_guidelines


FIXER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are the Fixer Agent in a professional
multi-agent code review system.

Your responsibility is to improve submitted code
using the Bug-Finder and Style/Lint reports.

Use the retrieved coding guidelines as supporting
reference material.

IMPORTANT INSTRUCTIONS:

1. Correct genuine syntax, logical and runtime bugs
   identified in the bug report.
2. Apply useful style and readability improvements.
3. Preserve the original program's intended behavior.
4. Do not introduce unnecessary complexity.
5. Do not blindly apply every suggestion.
6. Ignore incorrect or unsupported findings.
7. Do not invent requirements that were not provided.
8. Do not treat optional recommendations as mandatory.
9. If the original code is already correct, avoid
   unnecessary changes.
10. Do not execute the submitted code.
11. Return a complete corrected program.
12. Follow relevant retrieved coding guidelines.
13. Do not claim that a guideline is mandatory unless
    the retrieved context explicitly says so.
14. If no relevant guidelines are retrieved, use
    your general programming knowledge.

RESPONSE FORMAT:

1. SUMMARY OF CHANGES
Briefly explain what you corrected.

2. CORRECTED CODE
Provide the complete corrected program inside
a code block using the specified language.

3. EXPLANATION
Explain the important changes.

4. REMAINING CONCERNS
Mention any issues that could not be verified.
If there are none, explicitly say so.
        """
    ),
    (
        "human",
        """
Programming Language: {language}

RETRIEVED CODING GUIDELINES:
{guidelines}

ORIGINAL CODE:

```{language}
{code}
```

BUG-FINDER REPORT:

{bug_report}

STYLE/LINT REPORT:

{style_report}

Generate the improved program based on the
original code, the two reports and relevant
retrieved coding guidelines.
        """
    )
])


fixer_chain = FIXER_PROMPT | llm | StrOutputParser()


def fix_code(code, language, bug_report, style_report):

    if not code.strip():
        return "Please provide code to fix."

    # Retrieve guidelines relevant to the submitted code.
    guidelines_text = "No additional coding guidelines retrieved."

    if language == "Python":
        try:
            documents = retrieve_guidelines(
                f"Python code correction, error handling, "
                f"input validation, function design, "
                f"readability and best practices:\n"
                f"{code}\n{bug_report}\n{style_report}",
                k=3
            )

            if documents:
                guidelines_text = "\n\n".join(
                    document.page_content
                    for document in documents
                )

        except Exception as error:
            print(f"Guideline retrieval warning: {error}")

    # Generate the corrected program.
    result = fixer_chain.invoke({
        "code": code,
        "language": language,
        "bug_report": bug_report,
        "style_report": style_report,
        "guidelines": guidelines_text
    })

    return result
