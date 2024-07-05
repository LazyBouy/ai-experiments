import openai
from langchain_core.tools import tool


retriever = VectorStoreRetriever.from_docs(extract_docs(), openai.Client(base_url="http://localhost:11434"))

@tool
def lookup_policy(query: str, retriever: VectorStoreRetriever= retriever) -> str:
    """Consult the company policies to check whether certain options are permitted.
    Use this before making any flight changes performing other 'write' events."""
    
    docs = retriever.query(query, k=2)
    return "\n\n".join([doc["page_content"] for doc in docs])