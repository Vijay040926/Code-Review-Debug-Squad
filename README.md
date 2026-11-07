# Code Review & Debug Squad

A multi-agent code review and debugging application built with Python, Streamlit, LangChain, Groq, and ChromaDB.

The application accepts source code, analyzes it using specialized AI agents, suggests corrections, generates test cases, and (for supported languages) compiles or executes those tests locally.

## 1. Main features

The application includes four specialized agents:

- **Bug-Finder Agent** – identifies likely logical errors, runtime issues, edge cases, and input-validation problems.
- **Style/Lint Agent** – reviews naming, readability, formatting, organization, and maintainability.
- **Fixer Agent** – proposes corrected source code using the bug and style reports.
- **Test-Writer Agent** – generates test cases for the selected programming language.

It also includes a retrieval-augmented generation (RAG) component:

- Coding guidelines are stored in `data/coding_guidelines.txt`.
- `rag/vector_store.py` creates and accesses a persistent ChromaDB vector store.
- `rag/agentic_rag.py` decides whether a query needs guideline retrieval and then produces an answer using the retrieved context.

## 2. Technology stack

| Component | Technology |
|---|---|
| User interface | Streamlit |
| Programming language | Python |
| LLM provider | Groq API |
| LLM integration | LangChain and `langchain-groq` |
| Vector database | ChromaDB |
| Embeddings | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` |
| Python test execution | pytest |
| C compiler | GCC |
| C++ compiler | G++ |
| Java compiler/runtime | `javac` and `java` |
| JavaScript runtime | Node.js |

The application uses the Groq-hosted model configured in `utils/llm.py`. The model name may need to be updated there if the provider changes model availability.

## 3. Project structure

```text
Code-Review-Debug-Squad/
│
├── app.py                       # Streamlit application entry point
├── requirements.txt              # Python package dependencies
├── README.md                     # Project documentation
├── .env.example                  # Template for the Groq API key
├── .gitignore                    # Files excluded from sharing/version control
│
├── agents/
│   ├── __init__.py
│   ├── bug_finder.py              # Bug analysis agent
│   ├── style_lint.py              # Code style review agent
│   ├── fixer.py                   # Code correction agent
│   └── test_writer.py             # Test generation and repair
│
├── rag/
│   ├── __init__.py
│   ├── agentic_rag.py             # Retrieval decision and RAG response
│   └── vector_store.py            # ChromaDB and embedding setup
│
├── utils/
│   ├── __init__.py
│   ├── llm.py                     # Groq/LangChain configuration
│   └── code_executor.py           # Language-specific test execution
│
├── data/
│   └── coding_guidelines.txt      # Knowledge base used by RAG
│
└── [optional test scripts]       # Development and component checks
```

The `chroma_db/` directory is generated automatically when the vector store is initialized. It does not need to be submitted; it can be recreated from the coding-guidelines file.

## 4. Software prerequisites

Install the following on the computer that will run the project:

1. **Python 3.12** (or a compatible Python 3 version).
2. **GCC** for C programs, available through MinGW on Windows.
3. **G++** for C++ programs, available through MinGW on Windows.
4. **JDK** providing both `javac` and `java`.
5. **Node.js** for JavaScript execution.
6. **Internet access** for Groq API requests and the first-time download of the embedding model.

Check that the tools are available from Windows Command Prompt (CMD):

```cmd
python --version
gcc --version
g++ --version
javac -version
java -version
node --version
```

If a command is not recognized, install the corresponding tool and add its executable directory to the Windows `PATH`.

## 5. Installation on Windows

Open **Command Prompt (CMD)** and change to the extracted project directory:

```cmd
cd path\to\Code-Review-Debug-Squad
```

Create a virtual environment:

```cmd
python -m venv venv
```

Activate it:

```cmd
venv\Scripts\activate.bat
```

Install the required Python packages:

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The virtual environment is local to the computer. It is not included in the submission ZIP; each user creates their own environment using the commands above.

## 6. Groq API key configuration

The application requires a Groq API key to access the hosted language model.

1. Create or obtain a Groq API key from the Groq developer console.
2. In the project root, make a copy of `.env.example` and name the copy `.env`.
3. Open `.env` and replace the placeholder with the API key:

```text
GROQ_API_KEY=your_groq_api_key_here
```

4. Save the file.

**Important security note:** Do not email, upload, or commit your actual `.env` file. It contains a private API key. Share only `.env.example`; the person running the project must configure their own key. Never paste the key into source code or screenshots.

## 7. Run the application

With the virtual environment activated and the API key configured, run:

```cmd
streamlit run app.py
```

Streamlit will display a local URL in the terminal, usually:

```text
http://localhost:8501
```

Open that address in a web browser. Keep the CMD window open while using the application.

## 8. Supported language execution

The application can generate and execute test harnesses for the following languages, provided the required compiler/runtime is installed and available in `PATH`:

| Language | Compiler/runtime | Typical execution |
|---|---|---|
| Python | Python + pytest | Runs generated pytest tests |
| C | GCC | Compiles the C solution and test harness, then runs it |
| C++ | G++ | Compiles the C++ solution and test harness, then runs it |
| Java | JDK (`javac`, `java`) | Compiles the solution and test runner, then runs the test runner |
| JavaScript | Node.js | Runs the combined solution and test harness |

Select the language that matches the submitted source code in the application. The test generator and executor must use compatible source and test-harness formats.

## 9. RAG and first-time startup

The coding-guidelines knowledge base is stored in:

```text
data\coding_guidelines.txt
```

The embedding model is downloaded through Hugging Face the first time the vector store is initialized. This requires an internet connection and may take some time. ChromaDB data is then persisted locally in `chroma_db/`.

If `chroma_db/` is deleted, the application can rebuild the vector store from the coding-guidelines file when it runs again. The first rebuild may download/load the embedding model again.

## 10. Optional component checks

## Component Testing

The `tests/` directory contains individual verification scripts used during development to check the functionality of the project's major components.

| Test file | Component verified |
|---|---|
| `test_llm.py` | Groq LLM integration |
| `test_rag.py` | ChromaDB vector retrieval |
| `test_agentic_rag.py` | Agentic RAG workflow |
| `test_bug_finder_rag.py` | Bug-Finder Agent |
| `test_style_rag.py` | Style/Lint Agent |
| `test_fixer_rag.py` | Fixer Agent |
| `test_test_writer_rag.py` | Test-Writer Agent |

These scripts are optional and are not required to launch the Streamlit application.

To execute an individual component test, activate the virtual environment, configure the Groq API key in `.env`, and run the corresponding script from the project root.

For example:

```cmd
python tests\test_llm.py
python tests\test_agentic_rag.py
```

Some tests require an active internet connection and a valid Groq API key.

These are development/verification scripts for checking individual components. They are not required to launch the Streamlit interface. Run a script from the project root with the virtual environment activated, for example:


Some checks call the Groq API and therefore require a valid `.env` file and internet access.

## 11. Important execution and security limitations

- The LLM can produce incorrect or incomplete suggestions. Review generated changes before using them.
- Generated tests only check the cases they contain; passing tests do not prove that a program is completely correct.
- Local compilation/execution uses temporary files and time limits. It is **not a secure sandbox**. Do not run unknown or untrusted code with this application.
- Compiler errors may occur if generated test code does not match the submitted program's function names, class names, signatures, or language.
- Groq model availability, API limits, and pricing are controlled by the provider and may change.
- A working internet connection is required for hosted LLM requests and initial embedding-model setup.

## 12. Submission checklist

Before sharing the project:

- Include the source folders: `agents/`, `rag/`, `utils/`, and `data/`.
- Include `app.py`, `requirements.txt`, `README.md`, and `.env.example`.
- Include `.gitignore`.
- Do **not** include `venv/`, `.env`, `__pycache__/`, or `.pyc` files.
- `chroma_db/` can be omitted because it is generated from the knowledge-base file.
- Include optional test scripts if the reviewer should be able to run the component checks.
- Do not include personal API keys or other credentials.

## 13. Quick start summary

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
notepad .env
streamlit run app.py
```

Before running, add your own Groq API key to `.env` and ensure GCC, G++, the JDK, and Node.js are installed and available in `PATH`.
