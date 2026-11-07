
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key not found. Check your .env file.")

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.2,
    api_key=api_key
)

def get_llm_response(prompt):
    response = llm.invoke(prompt)
    return response.content
