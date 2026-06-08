from dotenv import load_dotenv
import os
import chromadb
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage,AIMessage
from functools import lru_cache

load_dotenv()  # loads GROQ_API_KEY from .env file

#connecting chromadb
@lru_cache(maxsize=1) #shared conn safe for reads
def get_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("support_faqs")
    return collection

#getting similar documents from chromadb
def retrieve(question):
    collection=get_collection()
    results=collection.query(query_texts=[question],n_results=1)
    context= "\n\n---\n\n".join(results["documents"][0])
    sources = []
    for i, doc in enumerate(results["documents"][0]):
        sources.append({
            "text": doc,
            "category": results["metadatas"][0][i]["category"],
            "intent": results["metadatas"][0][i]["intent"]
        })
    return context, sources

def ask(question,history=None):
    # Step 1: retrieve relevant chunks
    context,sources = retrieve(question)

    # Step 2: build the prompt
    system_prompt = f"""You are a helpful customer support agent for ShopEase.
Use ONLY the context below to answer the user's question.
If the answer is not in the context, say "I don't have information
about that — let me connect you to a human agent."
Keep answers concise and friendly.

Context:
{context}
"""
    messages=[SystemMessage(content=system_prompt)]
    if history:
        for turn in history:
            if turn['role']=='user':
                messages.append(HumanMessage(content=turn['content']))
            else:
                messages.append(AIMessage(content=turn['content']))
    messages.append(HumanMessage(content=question))
    # Step 3: invoke the LLM
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
    response = llm.invoke(messages)
    answer = response.content
    
    # Replace dataset placeholders with real values
    answer = answer.replace("{{Customer Support Hours}}", "9am-6pm IST, Mon-Fri")
    answer = answer.replace("{{Customer Support Phone Number}}", "1-800-SHOPEASE")
    answer = answer.replace("{{Website URL}}", "www.shopease.com")
    answer = answer.replace("{{Order Number}}", "your order number")
    answer = answer.replace("{{Live Chat}}", "Live Chat on our website")
    # after building sources list in retrieve(), or in ask() after getting sources:
    for source in sources:
        source["text"] = source["text"].replace("{{Order Number}}", "your order number")
        source["text"] = source["text"].replace("{{Customer Support Hours}}", "9am-6pm IST")
        source["text"] = source["text"].replace("{{Website URL}}", "www.shopease.com")
        source["text"] = source["text"].replace("{{Customer Support Phone Number}}", "1-800-SHOPEASE")
        source["text"] = source["text"].replace("{{Online Order Interaction}}", "Orders section")
        source["text"] = source["text"].replace("{{Online Company Portal Info}}", "our website")
    
    return answer,sources
  
if __name__ == "__main__":
    print(ask("my package hasn't arrived"))