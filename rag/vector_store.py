
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from functools import lru_cache

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Source knowledge base
GUIDELINES_FILE = BASE_DIR / "data" / "coding_guidelines.txt"

# Persistent ChromaDB storage
CHROMA_DIRECTORY = BASE_DIR / "chroma_db"

# Collection name
COLLECTION_NAME = "coding_guidelines"

@lru_cache(maxsize=1)
def get_embeddings():

    """
    Initialize the local embedding model.
    """

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    return embeddings


def load_guidelines():

    """
    Read the coding guidelines and convert them into documents.
    """

    if not GUIDELINES_FILE.exists():
        raise FileNotFoundError(
            f"Guidelines file not found: {GUIDELINES_FILE}"
        )

    text = GUIDELINES_FILE.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError("The coding guidelines file is empty.")

    document = Document(
        page_content=text,
        metadata={"source": str(GUIDELINES_FILE.name)}
    )

    return [document]


def split_guidelines(documents):

    """
    Divide documents into smaller chunks.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80
    )

    chunks = splitter.split_documents(documents)

    return chunks

@lru_cache(maxsize=1)
def get_vector_store():

    """
    Create or load the persistent ChromaDB vector store.

    Existing documents are not added again on every run.
    """

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIRECTORY)
    )

    existing_documents = vector_store.get()

    if not existing_documents["ids"]:

        print("Building the coding guidelines knowledge base...")

        documents = load_guidelines()

        chunks = split_guidelines(documents)

        vector_store.add_documents(chunks)

        print(f"Stored {len(chunks)} guideline chunks in ChromaDB.")

    else:

        print(
            f"Loaded existing knowledge base with "
            f"{len(existing_documents['ids'])} chunks."
        )

    return vector_store


def retrieve_guidelines(query, k=3):

    """
    Retrieve the most relevant coding guidelines for a query.
    """

    if not query.strip():
        return []

    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query,
        k=k
    )

    return results
