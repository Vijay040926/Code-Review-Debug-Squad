
from rag.vector_store import (
    get_vector_store,
    retrieve_guidelines
)


print("\nInitializing ChromaDB...\n")

# Create or load the vector database
vector_store = get_vector_store()

# Display stored document count
stored_data = vector_store.get()

print("Total stored chunks:", len(stored_data["ids"]))


# Test semantic retrieval
query = "How should I handle empty inputs and exceptions in Python?"

print("\nSearch Query:")
print(query)

results = retrieve_guidelines(query, k=3)

print("\nRetrieved Guidelines:\n")

for index, document in enumerate(results, start=1):

    print(f"Result {index}")
    print("Source:", document.metadata.get("source"))
    print("Content:", document.page_content)
    print("-" * 60)
