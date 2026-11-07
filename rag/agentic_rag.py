
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm import llm
from rag.vector_store import retrieve_guidelines


# --------------------------------------------------
# 1. Retrieval Decision Prompt
# --------------------------------------------------

RETRIEVAL_DECISION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are the Retrieval Decision Agent in a
        Code Review and Debugging system.

        Your responsibility is to decide whether a user's
        query requires information from the coding guidelines
        knowledge base.

        Choose RETRIEVE when the query concerns:
        - Python coding standards
        - PEP 8 recommendations
        - Naming conventions
        - Code readability
        - Error handling practices
        - Function design
        - Code optimization
        - Security practices
        - Testing practices
        - Maintainability

        Choose SKIP when:
        - The query is unrelated to coding guidelines.
        - The answer requires only simple general knowledge.
        - The query is a basic calculation.
        - Retrieved guidelines would not improve the answer.

        IMPORTANT:
        Return exactly ONE word:
        RETRIEVE or SKIP.

        Do not provide explanations.
        """
    ),
    (
        "human",
        """
        User Query:

        {query}

        Should the coding guidelines knowledge base
        be consulted?
        """
    )
])


# --------------------------------------------------
# 2. RAG Response Prompt
# --------------------------------------------------

RAG_RESPONSE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an intelligent coding assistant.

        Answer the user's query accurately and clearly.

        You may receive coding guidelines retrieved from
        the ChromaDB knowledge base.

        Instructions:

        1. Use the retrieved guidelines when relevant.
        2. Do not invent information from the knowledge base.
        3. If no guidelines are supplied, answer using
           your general programming knowledge.
        4. Distinguish recommendations from mandatory rules.
        5. Provide examples when useful.
        6. Keep the answer understandable for students.
        7. Do not claim that a recommendation is mandatory
           unless the retrieved context explicitly says so.

        8. Clearly distinguish information retrieved from
           the knowledge base from additional general knowledge.
        
        9. Avoid adding unrelated coding guidelines.
        
        10. Keep responses concise unless the user asks
            for a detailed explanation.

        If retrieved context is available, use it to
        support your answer.
        """
    ),
    (
        "human",
        """
        USER QUERY:

        {query}

        RETRIEVED CODING GUIDELINES:

        {context}

        Provide your answer.
        """
    )
])


# --------------------------------------------------
# 3. Build LCEL Chains
# --------------------------------------------------

retrieval_decision_chain = (
    RETRIEVAL_DECISION_PROMPT
    | llm
    | StrOutputParser()
)

rag_response_chain = (
    RAG_RESPONSE_PROMPT
    | llm
    | StrOutputParser()
)


# --------------------------------------------------
# 4. Agentic RAG Workflow
# --------------------------------------------------

def run_agentic_rag(query):

    if not query.strip():
        return {
            "decision": "SKIP",
            "retrieved_documents": [],
            "answer": "Please enter a query."
        }

    # Step 1: Decide whether retrieval is necessary

    decision = retrieval_decision_chain.invoke({
        "query": query
    })

    decision = decision.strip().upper().split()[0]

    if decision not in {"RETRIEVE", "SKIP"}:
        raise ValueError(
            f"Invalid retrieval decision returned: {decision}"
        )

    # Step 2: Retrieve guidelines only when necessary

    retrieved_documents = []

    if decision == "RETRIEVE":

        retrieved_documents = retrieve_guidelines(
            query,
            k=3
        )

    # Step 3: Prepare retrieved context

    if retrieved_documents:

        context = "\n\n".join(
            document.page_content
            for document in retrieved_documents
        )

    else:

        context = "No additional coding guidelines retrieved."

    # Step 4: Generate the final response

    answer = rag_response_chain.invoke({
        "query": query,
        "context": context
    })

    # Step 5: Return answer and retrieval information

    return {
        "decision": decision,
        "retrieved_documents": retrieved_documents,
        "answer": answer
    }
