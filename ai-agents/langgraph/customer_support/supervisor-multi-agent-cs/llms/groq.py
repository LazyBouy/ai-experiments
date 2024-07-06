from langchain_groq import ChatGroq

llm_model = "llama3-70b-8192" 
#llm_model = "mixtral-8x7b-32768"
#llm_model = "gemma-7b-it"
groq_llm = ChatGroq(
    temperature=0,
    model=llm_model
)