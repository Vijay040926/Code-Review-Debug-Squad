import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path


LANGUAGE_ALIASES = {
    "Python": {"python", "py"},
    "C": {"c"},
    "C++": {"cpp", "c++", "cc"},
    "Java": {"java"},
    "JavaScript": {"javascript", "js", "node"},
}


def _extract_fenced_code(response, language=None):
    """Extract a code block, preferring a fence tagged for the selected language."""
    if not isinstance(response, str) or not response.strip():
        raise ValueError("The AI response did not contain any code.")

    pattern = r"```([A-Za-z0-9_+#.-]*)[ \t]*\r?\n(.*?)```"
    matches = re.findall(pattern, response, flags=re.DOTALL)

    if not matches:
        # Accept plain code only when the response contains no Markdown fence.
        if "```" not in response:
            return response.strip()
        raise ValueError("Could not extract a complete code block from the AI response.")

    if language:
        aliases = LANGUAGE_ALIASES.get(language, {language.lower()})
        for tag, body in matches:
            if tag.lower() in aliases:
                return body.strip()

    return matches[0][1].strip()


def extract_python_code(response):
    code = _extract_fenced_code(response, "Python")
    ast.parse(code)
    return code


def extract_language_code(response, language):
    """Extract corrected source code for any language supported by the GUI."""
    if language == "Python":
        return extract_python_code(response)
    if language not in LANGUAGE_ALIASES:
        raise ValueError(f"Unsupported programming language: {language}")
    return _extract_fenced_code(response, language)


def extract_test_code(response, language="Python"):
    """Extract generated test code. Python tests are additionally AST-parsed."""
    test_code = _extract_fenced_code(response, language)
    if language == "Python":
        ast.parse(test_code)
    return test_code


def validate_test_code(test_code):
    tree = ast.parse(test_code)
    allowed_imports = {"pytest", "solution", "math"}

    test_functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]

    if not test_functions:
        raise ValueError(
            "The Test-Writer did not generate any pytest test functions."
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in allowed_imports:
                    raise ValueError(f"Test import not allowed: {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                raise ValueError("Relative imports are not allowed.")
            if node.module.split(".")[0] not in allowed_imports:
                raise ValueError(f"Test import not allowed: {node.module}")

        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {
                "eval", "exec", "compile", "open", "__import__", "input"
            }:
                raise ValueError(
                    f"Unsafe function call detected: {node.func.id}"
                )

    return True


def _result(status, output="", error="", return_code=-1):
    return {
        "status": status,
        "output": output or "",
        "error": error or "",
        "return_code": return_code,
    }


def run_pytest(corrected_code, test_code, timeout=30):
    try:
        ast.parse(corrected_code)
        ast.parse(test_code)
        validate_test_code(test_code)

        with tempfile.TemporaryDirectory() as temp_dir:
            solution_path = Path(temp_dir) / "solution.py"
            test_path = Path(temp_dir) / "test_solution.py"

            solution_path.write_text(corrected_code, encoding="utf-8")
            test_path.write_text(test_code, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable, "-I", "-m", "pytest", "-q",
                    "--tb=short", str(test_path)
                ],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )

            if result.returncode == 0:
                status = "PASS"
            elif result.returncode == 1:
                status = "FAIL"
            elif result.returncode == 5:
                status = "NO TESTS"
            else:
                status = "ERROR"

            return _result(status, result.stdout, result.stderr, result.returncode)

    except subprocess.TimeoutExpired:
        return _result(
            "TIMEOUT", error=f"Tests exceeded the {timeout}-second time limit."
        )
    except Exception as error:
        return _result("ERROR", error=str(error))



def _looks_like_cpp(code):
    """Detect clear C++ syntax when the GUI selection says C by mistake."""
    if not isinstance(code, str):
        return False

    cpp_markers = (
        r"#\s*include\s*<\s*(iostream|vector|string|algorithm|stdexcept|map|set|memory)\s*>",
        r"\bstd\s*::",
        r"\bstd\s*::\s*vector\b",
        r"\busing\s+namespace\s+std\s*;",
        r"\bcout\b|\bcin\b",
        r"\bclass\s+[A-Za-z_]\w*",
        r"\bnamespace\s+[A-Za-z_]\w*",
        r"\btemplate\s*<",
    )
    return any(re.search(pattern, code) for pattern in cpp_markers)


def _normalize_solution_include(test_code, language):
    """Point generated harness includes at the temporary solution filename."""
    if language == "C++":
        target = "solution.cpp"
        pattern = r'(#\s*include\s*")([^"]+\.(?:cpp|cc|cxx))(")'
    else:
        target = "solution.c"
        pattern = r'(#\s*include\s*")([^"]+\.c)(")'

    return re.sub(pattern, lambda match: match.group(1) + target + match.group(3),
                  test_code, flags=re.IGNORECASE)


def run_language_tests(corrected_code, test_code, language, timeout=20):
    """
    Compile/run generated tests for C, C++, Java and JavaScript.
    The generated harness format is defined in agents/test_writer.py.
    """
    if language == "Python":
        return run_pytest(corrected_code, test_code, timeout=max(timeout, 30))

    if language not in {"C", "C++", "Java", "JavaScript"}:
        return _result("ERROR", error=f"Unsupported language: {language}")

    # If the user selected C but the LLM returned unmistakable C++ code,
    # route both source and test harness through the C++ compiler.
    effective_language = language
    if language == "C" and (
        _looks_like_cpp(corrected_code) or _looks_like_cpp(test_code)
    ):
        effective_language = "C++"

    language = effective_language
    if language in {"C", "C++"}:
        test_code = _normalize_solution_include(test_code, language)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            workdir = Path(temp_dir)

            if language == "C":
                solution_path = workdir / "solution.c"
                test_path = workdir / "test_runner.c"
                executable = workdir / "test_runner.exe"
                solution_path.write_text(corrected_code, encoding="utf-8")
                test_path.write_text(test_code, encoding="utf-8")
                compile_command = [
                    "gcc", "-std=c99", "-Wall", "-Wextra",
                    str(test_path), "-o", str(executable)
                ]
                run_command = [str(executable)]

            elif language == "C++":
                solution_path = workdir / "solution.cpp"
                test_path = workdir / "test_runner.cpp"
                executable = workdir / "test_runner.exe"
                solution_path.write_text(corrected_code, encoding="utf-8")
                test_path.write_text(test_code, encoding="utf-8")
                compile_command = [
                    "g++", "-std=c++11", "-Wall", "-Wextra",
                    str(test_path), "-o", str(executable)
                ]
                run_command = [str(executable)]

            elif language == "Java":
                class_match = re.search(
                    r"\bpublic\s+class\s+([A-Za-z_$][\w$]*)", corrected_code
                )
                if not class_match:
                    class_match = re.search(
                        r"\bclass\s+([A-Za-z_$][\w$]*)", corrected_code
                    )
                if not class_match:
                    return _result(
                        "ERROR",
                        error="Could not identify a Java class in the corrected code."
                    )

                class_name = class_match.group(1)
                solution_path = workdir / f"{class_name}.java"
                test_path = workdir / "TestRunner.java"
                solution_path.write_text(corrected_code, encoding="utf-8")
                test_path.write_text(test_code, encoding="utf-8")
                compile_command = [
                    "javac", str(solution_path), str(test_path)
                ]
                run_command = ["java", "-cp", str(workdir), "TestRunner"]

            else:  # JavaScript
                combined_path = workdir / "combined_test.js"
                combined_path.write_text(
                    corrected_code + "\n\n" + test_code + "\n",
                    encoding="utf-8",
                )
                compile_command = None
                run_command = ["node", str(combined_path)]

            if compile_command is not None:
                try:
                    compilation = subprocess.run(
                        compile_command,
                        cwd=workdir,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        shell=False,
                    )
                except FileNotFoundError as error:
                    return _result(
                        "ERROR",
                        error=(
                            f"Required compiler/runtime was not found: {error}. "
                            "Check that it is available in Windows PATH."
                        ),
                    )

                if compilation.returncode != 0:
                    return _result(
                        "COMPILE ERROR",
                        compilation.stdout,
                        compilation.stderr,
                        compilation.returncode,
                    )

            try:
                execution = subprocess.run(
                    run_command,
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=False,
                )
            except FileNotFoundError as error:
                return _result(
                    "ERROR",
                    error=(
                        f"Required compiler/runtime was not found: {error}. "
                        "Check that it is available in Windows PATH."
                    ),
                )

            status = "PASS" if execution.returncode == 0 else "FAIL"
            compile_output = ""
            if language in {"C", "C++"}:
                # Keep compiler warnings visible without treating them as failures.
                compile_output = compilation.stdout + compilation.stderr

            return _result(
                status,
                compile_output + execution.stdout,
                execution.stderr,
                execution.returncode,
            )

    except subprocess.TimeoutExpired:
        return _result(
            "TIMEOUT",
            error=f"Compilation or test execution exceeded {timeout} seconds.",
        )
    except Exception as error:
        return _result("ERROR", error=str(error))
