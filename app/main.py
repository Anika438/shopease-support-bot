from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from app.rag import ask
from app.agent import run_agent
from app.database import init_db, save_message, get_history,clear_history,init_orders_db,get_order
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
load_dotenv()

init_db()  # creates table at startup
init_orders_db() # creates orders table and sample data

class ChatRequest(BaseModel):
  message: str
  session_id: str = 'default'

class ChatResponse(BaseModel):
  answer: str
  sources: list
  mode: str="RAG"

app = FastAPI(title="ShopEase Support Chatbot")

@app.get('/health')
async def health():
  return {'status': 'ok'}

# @app.post('/chat',response_model=ChatResponse)
# async def chat(request: ChatRequest):
#   try:
#     history=get_history(request.session_id)
#     answer,sources = ask(request.message,history=history)
#     save_message(request.session_id,'user',request.message)
#     save_message(request.session_id,'assistant',answer)
#     return ChatResponse(answer=answer,sources=sources)
#   except Exception as e:
#     raise HTTPException(status_code=500, detail=str(e))

@app.get('/history/{session_id}')
async def get_session_history(session_id :str):
  history=get_history(session_id)
  return {'messages': history}

@app.delete('/history/{session_id}')
async def clear(session_id:str):
  clear_history(session_id)
  return {'status': 'cleared'}


def is_action_query(message: str,history=None) -> bool:
  try:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY")
    )
    context = ""
    if history:
      context = "\n".join([
      f"{h['role'].upper()}: {h['content']}" 
      for h in history
      ])
    prompt = f"""Classify this customer message. Reply ONLY with ACTION or FAQ.
ACTION = checking order status, cancelling order, updating shipping address
FAQ = general questions about policies, refunds, payments, procedures
Full conversation so far:
{context}

New message: {message}

Classification:"""
    
    result = llm.invoke(prompt)
    classification = result.content.strip().upper()
    return "ACTION" in classification
  except Exception as e:
      print(f"Error in is_action_query: {e}")
      return False

@app.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        history = get_history(request.session_id)
        
        if is_action_query(request.message,history=history):
            recent_history = history[-4:] if history else []
            answer = run_agent(request.message, history=recent_history)
            sources = []
            mode="Agent"
        else:
            answer, sources = ask(request.message, history=history)
            mode="RAG"

        save_message(request.session_id, 'user', request.message)
        save_message(request.session_id, 'assistant', answer)
        return ChatResponse(answer=answer, sources=sources, mode=mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
