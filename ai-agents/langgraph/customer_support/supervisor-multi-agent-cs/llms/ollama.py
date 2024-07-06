from langchain_community.chat_models import ChatOllama

# Specify the local language model
local_llm =  "llama3:8b" #"phi3:latest"
ollama_llm = ChatOllama(model=local_llm, format="json", temperature=0)