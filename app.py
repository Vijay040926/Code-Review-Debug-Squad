import streamlit as st

from utils.llm import get_llm_response
from agents.bug_finder import find_bugs
from agents.style_lint import review_style
from agents.fixer import fix_code
from agents.test_writer import (
    generate_tests,
    generate_language_tests,
    repair_tests,
)
from utils.code_executor import (
    extract_python_code,
    extract_language_code,
    extract_test_code,
    validate_test_code,
    run_pytest,
    run_language_tests,
)


st.set_page_config(
    page_title="Code Review & Debug Squad",
    page_icon="💻",
    layout="wide",
)


def generate_validated_tests(corrected_code):
    """Generate and validate Python pytest tests, repairing once if needed."""
    test_response = generate_tests(corrected_code)
    generated_test_code = extract_test_code(test_response, "Python")

    for attempt in range(2):
        try:
            validate_test_code(generated_test_code)
            return generated_test_code
        except Exception as validation_error:
            if attempt == 1:
                raise
            repaired_response = repair_tests(
                corrected_code,
                generated_test_code,
                str(validation_error),
            )
            generated_test_code = extract_test_code(
                repaired_response, "Python"
            )

    return generated_test_code


def generate_tests_for_language(source_code, selected_language):
    """Use pytest for Python and a native executable harness for other languages."""
    if selected_language == "Python":
        return generate_validated_tests(source_code)

    response = generate_language_tests(source_code, selected_language)
    return extract_test_code(response, selected_language)


def streamlit_code_language(selected_language):
    return {
        "Python": "python",
        "C": "c",
        "C++": "cpp",
        "Java": "java",
        "JavaScript": "javascript",
    }[selected_language]


st.title("Code Review & Debug Squad")
st.caption(
    "AI-powered multi-agent code review, debugging and automated testing assistant"
)
st.divider()

st.sidebar.header("Project Information")
st.sidebar.write("Multi-Agent AI Code Assistant")
st.sidebar.write("Powered by Groq and LangChain")
st.sidebar.divider()
st.sidebar.subheader("Available Agents")
st.sidebar.write("1. Bug-Finder Agent")
st.sidebar.write("2. Style/Lint Agent")
st.sidebar.write("3. Fixer Agent")
st.sidebar.write("4. Test-Writer Agent")
st.sidebar.divider()
st.sidebar.caption("Knowledge Base: ChromaDB")
st.sidebar.caption(
    "Execution note: run only code you trust. Time limits are enabled, "
    "but local execution is not a secure sandbox."
)

st.subheader("Submit Your Code")

language = st.selectbox(
    "Select Programming Language",
    ["Python", "Java", "C", "C++", "JavaScript"],
)

operation = st.selectbox(
    "Choose an operation",
    [
        "Debug Code",
        "Style/Lint Review",
        "Review Code",
        "Fix Code",
        "Explain Code",
        "Generate Test Cases",
    ],
)

code = st.text_area(
    "Paste Your Code Here",
    height=300,
    placeholder="Enter your code snippet...",
)

if st.button("Analyze Code", type="primary"):
    if not code.strip():
        st.warning("Please enter some code before submitting.")
    else:
        result = ""
        test_result = None
        generated_test_code = None

        try:
            if operation == "Debug Code":
                with st.spinner("Bug-Finder Agent is analyzing..."):
                    result = find_bugs(code, language)

            elif operation == "Style/Lint Review":
                with st.spinner("Style/Lint Agent is reviewing..."):
                    result = review_style(code, language)

            elif operation == "Review Code":
                with st.status(
                    "Running the review agents...", expanded=True
                ) as status:
                    st.write("Bug-Finder Agent is examining the code...")
                    bug_report = find_bugs(code, language)

                    st.write("Style/Lint Agent is reviewing the code...")
                    style_report = review_style(code, language)

                    result = (
                        "## Bug-Finder Report\n\n"
                        + bug_report
                        + "\n\n---\n\n"
                        + "## Style/Lint Report\n\n"
                        + style_report
                    )
                    status.update(
                        label="Code review completed!", state="complete"
                    )

            elif operation == "Fix Code":
                with st.status(
                    "Running the complete agent workflow...", expanded=True
                ) as status:
                    st.write("Step 1: Bug-Finder Agent is examining the code...")
                    bug_report = find_bugs(code, language)

                    st.write("Step 2: Style/Lint Agent is reviewing the code...")
                    style_report = review_style(code, language)

                    st.write("Step 3: Fixer Agent is generating corrected code...")
                    result = fix_code(
                        code, language, bug_report, style_report
                    )

                    st.write("Step 4: Extracting corrected source code...")
                    corrected_code = extract_language_code(result, language)

                    st.write("Step 5: Test-Writer Agent is generating executable tests...")
                    generated_test_code = generate_tests_for_language(
                        corrected_code, language
                    )

                    st.write("Step 6: Compiling/running the generated tests...")
                    test_result = run_language_tests(
                        corrected_code, generated_test_code, language
                    )

                    status.update(
                        label="Agent workflow completed!", state="complete"
                    )

            elif operation == "Explain Code":
                prompt = f"""
You are an experienced programming tutor.
Explain the following {language} code in beginner-friendly language.

Cover:
1. Purpose of the program.
2. Explanation of important statements.
3. Functions and variables.
4. Program execution flow.
5. Expected output, where applicable.

CODE:
{code}
"""
                with st.spinner("Generating code explanation..."):
                    result = get_llm_response(prompt)

            elif operation == "Generate Test Cases":
                with st.status(
                    "Generating and executing test cases...", expanded=True
                ) as status:
                    st.write("Step 1: Test-Writer Agent is generating executable tests...")
                    generated_test_code = generate_tests_for_language(
                        code, language
                    )

                    st.write("Step 2: Running the tests against the submitted code...")
                    test_result = run_language_tests(
                        code, generated_test_code, language
                    )

                    result = (
                        "Executable test cases were generated. "
                        "Their results are shown below."
                    )
                    status.update(
                        label="Test generation and execution completed!",
                        state="complete",
                    )

            st.success("Analysis completed!")
            st.subheader("AI Analysis")
            st.markdown(result)

            if generated_test_code:
                st.divider()
                st.subheader("Generated Test Cases")
                st.code(
                    generated_test_code,
                    language=streamlit_code_language(language),
                )

            if test_result is not None:
                st.divider()
                st.subheader("Automated Testing Results")

                if test_result["status"] == "PASS":
                    st.success("All generated tests passed!")
                elif test_result["status"] == "FAIL":
                    st.error("One or more generated tests failed.")
                elif test_result["status"] == "COMPILE ERROR":
                    st.error("The generated test harness or solution did not compile.")
                elif test_result["status"] == "TIMEOUT":
                    st.warning("Compilation or test execution timed out.")
                elif test_result["status"] == "NO TESTS":
                    st.warning("No executable test cases were found.")
                else:
                    st.error("Test execution encountered an error.")

                if test_result["output"]:
                    st.write(
                        "Pytest / Compiler / Runtime Output:"
                    )
                    st.code(test_result["output"])

                if test_result["error"]:
                    st.write("Execution Details:")
                    st.code(test_result["error"])

        except Exception as error:
            st.error(
                "Something went wrong while processing your request."
            )
            st.exception(error)

st.divider()
st.caption("Code Review & Debug Squad | Academic Project")
