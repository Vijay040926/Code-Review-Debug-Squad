from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm import llm
from rag.vector_store import retrieve_guidelines


TEST_WRITER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are the Test-Writer Agent in a professional Python code review system.

Generate meaningful executable pytest tests for the INTENDED functionality
of the submitted Python program, not its current buggy behavior.

Rules:
1. Generate at least five test functions, each named test_*.
2. Cover normal inputs and relevant edge cases.
3. Import the submitted module using: import solution
4. Call functions using: solution.function_name(...)
5. Use pytest assertions and appropriate exception checks.
6. Do not redefine the original functions.
7. Do not use os, sys, subprocess, file operations, eval or exec.
8. Return ONLY executable Python code, without Markdown fences.
9. Expected results must represent intended behavior, not existing bugs.
10. Do not weaken assertions just to make tests pass.
11. Do not test bool as numeric unless explicitly supported.
12. Avoid redundant or irrelevant tests.
        """
    ),
    (
        "human",
        """
RETRIEVED TESTING GUIDELINES:
{guidelines}

SUBMITTED PYTHON CODE:
{code}

Generate tests for the intended functionality.
        """
    )
])


REPAIR_TEST_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You repair Python pytest code while preserving the intended behavior tested.

Rules:
- Always use `import solution`, then call solution.function_name(...).
- Every test function starts with test_.
- Preserve intended expected results; do not weaken valid assertions.
- Do not redefine submitted functions.
- Do not use os, sys, subprocess, open, eval or exec.
- Return ONLY executable Python code, without Markdown fences.
        """
    ),
    (
        "human",
        """
RETRIEVED TESTING GUIDELINES:
{guidelines}

ORIGINAL SOLUTION:
{code}

GENERATED TEST CODE:
{test_code}

VALIDATION ERROR:
{error}

Repair the test code without weakening its assertions.
        """
    )
])


MULTILANGUAGE_TEST_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a software testing engineer. Generate a SMALL, executable test harness
for the supplied {language} solution.

The submitted solution may contain bugs. Test the intended behavior inferred
from function names, comments, and the apparent purpose. Do not copy the
incorrect behavior of the current implementation into expected results.

GENERAL RULES:
- Generate at least five meaningful test cases where the function supports them.
- Include normal cases and relevant boundary cases (negative values, one item,
  duplicates, and empty input only if the function contract can handle it).
- Expected results must be correct for the intended functionality.
- Do not change the solution implementation.
- Do not use external test frameworks or third-party packages.
- Return ONLY executable source code for the test harness, without Markdown fences.
- Print a clear success message if every test passes.
- On a failed test, print the case and expected/actual values, then exit nonzero.
- Do not claim tests passed unless the harness actually checks them.

LANGUAGE-SPECIFIC HARNESS FORMAT:

For C:
- Return a complete C test-runner source file.
- Include the submitted source with:
  #define main original_program_main
  #include "solution.c"
  #undef main
- Include standard headers needed by the harness.
- Call the relevant function directly and check results.
- Do not define another copy of the solution function.

For C++:
- Return a complete C++ test-runner source file.
- Include the submitted source with:
  #define main original_program_main
  #include "solution.cpp"
  #undef main
- Include standard headers needed by the harness.
- Call the relevant function directly and check results.
- Do not define another copy of the solution function.

For Java:
- Return a separate Java source file containing a package-free class named TestRunner.
- The submitted source will be compiled alongside TestRunner.java.
- Call the appropriate method on the submitted class. Use a class instance if the method is not static.
- Do not define or copy the submitted class or its methods.
- Use ordinary checks and throw an AssertionError or exit nonzero when a check fails.
- Do not rely on Java's `assert` keyword because assertions may be disabled.

For JavaScript:
- Return a JavaScript test block that will be appended directly after the submitted source in the same file.
- Call the submitted function directly (do not use require/import for the solution).
- Wrap the entire test harness in an immediately invoked function expression (IIFE)
  so its variables cannot collide with top-level solution variables.
- Use Node's built-in `node:assert/strict` module inside that IIFE.
- Throw on a failed test and print a success message when all tests pass.

For all languages, adapt function names, parameter types, and calling conventions to the supplied code.
If the source does not expose a callable function that can reasonably be tested, explain that limitation in a code comment and return a minimal harness that exits nonzero rather than inventing an interface.
        """
    ),
    (
        "human",
        """
RETRIEVED TESTING GUIDELINES:
{guidelines}

LANGUAGE:
{language}

CORRECTED OR SUBMITTED SOURCE CODE:
{code}

Generate the executable test harness in the required format for {language}.
        """
    )
])


test_writer_chain = TEST_WRITER_PROMPT | llm | StrOutputParser()
repair_test_chain = REPAIR_TEST_PROMPT | llm | StrOutputParser()
multilanguage_test_chain = MULTILANGUAGE_TEST_PROMPT | llm | StrOutputParser()


def get_testing_guidelines(query):
    guidelines_text = "No additional testing guidelines retrieved."
    try:
        documents = retrieve_guidelines(
            "Software testing, test cases, normal inputs, boundary conditions, "
            f"empty inputs, negative numbers, exceptions and assertions:\n{query}",
            k=3,
        )
        if documents:
            guidelines_text = "\n\n".join(
                document.page_content for document in documents
            )
    except Exception as error:
        print(f"Guideline retrieval warning: {error}")
    return guidelines_text


def generate_tests(code):
    """Generate Python pytest tests (kept for backward compatibility)."""
    if not code.strip():
        raise ValueError("Please provide Python code.")
    guidelines_text = get_testing_guidelines(code)
    return test_writer_chain.invoke({
        "code": code,
        "guidelines": guidelines_text,
    })


def repair_tests(code, test_code, error):
    guidelines_text = get_testing_guidelines(f"{code}\n{test_code}\n{error}")
    return repair_test_chain.invoke({
        "code": code,
        "test_code": test_code,
        "error": error,
        "guidelines": guidelines_text,
    })


def generate_language_tests(code, language):
    """Generate an executable harness for C, C++, Java or JavaScript."""
    supported = {"C", "C++", "Java", "JavaScript"}
    if language not in supported:
        raise ValueError(
            f"Language-specific test generation is not configured for {language}."
        )
    if not code.strip():
        raise ValueError("Please provide source code.")

    guidelines_text = get_testing_guidelines(
        f"{language} test harness, unit tests, edge cases and assertions: {code}"
    )
    return multilanguage_test_chain.invoke({
        "code": code,
        "language": language,
        "guidelines": guidelines_text,
    })
