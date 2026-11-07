
from rag.agentic_rag import run_agentic_rag


test_queries = [
    "What are Python naming conventions?",
    "How should I handle exceptions in Python?",
    "What is 5 + 10?"
]


for query in test_queries:

    print("\n" + "=" * 60)

    print("USER QUERY:")
    print(query)

    result = run_agentic_rag(query)

    print("\nRETRIEVAL DECISION:")
    print(result["decision"])

    print("\nRETRIEVED DOCUMENTS:")

    if result["retrieved_documents"]:

        for document in result["retrieved_documents"]:
            print("-", document.metadata.get("source"))
            print(document.page_content)

    else:
        print("No documents retrieved.")

    print("\nAI RESPONSE:")
    print(result["answer"])

    print("=" * 60)
