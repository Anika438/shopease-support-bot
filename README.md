# ShopEase Support Bot 🛍️

An AI customer support chatbot combining RAG (Retrieval-Augmented Generation) with an agentic AI layer — built with FastAPI, ChromaDB, LangGraph, Groq, and Streamlit.

Rather than a traditional chatbot with predefined response tracks, ShopEase understands the **intent** behind every message and either answers from a knowledge base or takes real actions like checking order status, cancelling orders, or updating shipping addresses.

---

## What it does

- **FAQ answering** — Semantic search over 500 balanced customer support entries across 10 categories. Answers questions about returns, refunds, payments, shipping, and account management.
- **Order actions** — LangGraph agent with real database tools: check order status, cancel orders, update shipping addresses.
- **Hybrid routing** — LLM-based classifier routes each message to the right pipeline: RAG for FAQs, agent for order actions.
- **Persistent sessions** — Conversation history stored in SQLite, survives server restarts and browser reloads.
- **Source citations** — Every FAQ answer shows the retrieved source documents used to generate it.

---

## Architecture

```
User message
      ↓
Streamlit UI → POST /chat (FastAPI)
      ↓
LLM Classifier (llama-3.1-8b-instant)
      ↓
 ┌────────────────────────────────────┐
 │ FAQ query        │ Order action    │
 │                  │                 │
 │ RAG Pipeline     │ LangGraph Agent │
 │ ChromaDB search  │ check_order     │
 │ LLaMA 3.1 8b     │ cancel_order    │
 │                  │ update_address  │
 └────────────────────────────────────┘
      ↓
 Answer + Sources → Streamlit UI
      ↓
 SQLite (session + order persistence)
```

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| LLM | Groq (LLaMA 3.1 8b instant) | Free tier, fast inference, OpenAI-compatible |
| Vector DB | ChromaDB | Zero-setup local vector search, HNSW indexing |
| Orchestration | LangChain + LangGraph | Tool-calling agent, RAG chains |
| API | FastAPI | Async, auto-generates /docs, Pydantic validation |
| Frontend | Streamlit | Python-native chat UI, free cloud deployment |
| Database | SQLite | Zero-setup session + order persistence |
| Routing | LLM classifier | Intent-based routing, not brittle keyword matching |

---

## Evaluation

Retrieval accuracy measured on 17 held-out test cases (not in the ingested dataset):

**Result: 64.7% top-1 retrieval accuracy (11/17)**

Primary failure mode: semantic overlap between SHIPPING/DELIVERY and CANCEL/ORDER categories — a known limitation of single-vector retrieval. Production improvement: re-ranking with a cross-encoder or category-aware routing.

---

## Project Structure

```
shopease-support-bot/
├── app/
│   ├── ingest.py          
│   ├── rag.py           
│   ├── agent.py           
│   ├── database.py        
│   └── main.py            
├── streamlit_app.py       
├── eval.py                
├── shopease.db            
├── chroma_db/             
└── requirements.txt
```

---

## Setup

### Prerequisites
- Python 3.12
- Free Groq API key — [console.groq.com](https://console.groq.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/shopease-support-bot
cd shopease-support-bot

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt

# Set up environment
echo "GROQ_API_KEY=your_key_here" > .env
```

### Run

```bash
# Step 1 — ingest data (run once)
python app/ingest.py

# Step 2 — start API server
uvicorn app.main:app --reload --port 8000

# Step 3 — start frontend (new terminal)
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) to use the bot.
API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Evaluate retrieval

```bash
python eval.py
```

---

## Sample Interactions

**FAQ query (RAG mode):**
> User: how do I get a refund?
> Chuggy: To initiate a refund, please contact our support team with your order number...

**Order action (Agent mode):**
> User: what is the status of order ORD-1001?
> Chuggy: Order ORD-1001 — Blue Sneakers | Status: processing | Address: 123 MG Road, Mumbai

**Cancel order:**
> User: cancel order ORD-1002
> Chuggy: Order ORD-1002 has been successfully cancelled.

<!-- ---

## Design Decisions

**Why RAG instead of fine-tuning?**
RAG is faster to build, cheaper (no GPU training), and easier to update — add new docs without retraining. Fine-tuning is better for style changes; RAG is better for factual grounding in private data.

**Why LLM-based routing instead of keywords?**
Keyword routing is brittle. "I cancelled the order by mistake" contains "cancel" but means RESTORE not CANCEL. The LLM understands full context and intent.

**Why SQLite instead of Postgres?**
Single-server deployment, zero setup, built into Python. The database layer is abstracted (repository pattern in database.py) so swapping to Postgres means changing one file.

**Why ChromaDB's built-in embeddings instead of sentence-transformers?**
PyTorch is incompatible with Intel Mac + Python 3.12. ChromaDB's onnxruntime embeddings work without torch and perform adequately for this use case.

 -->
---
## Known Limitations

- **Agent token limits** — LangGraph agent uses llama-3.3-70b-versatile for reliable tool calling. Groq free tier has 100k tokens/day limit (~15-20 agent queries/day).
- **8b tool calling** — llama-3.1-8b-instant has inconsistent tool-call formatting. Single-parameter tools (check status, cancel) work reliably; multi-parameter tools (update address) require the 70b model.
- **Session storage** — Conversation history is stored in SQLite on the server. Scales to single-server deployments; production would use Redis.
- **Dataset placeholders** — The Bitext dataset uses {{placeholder}} template variables. Replaced at response time with hardcoded values.
- **Retrieval accuracy** — 64.7% on held-out test set. Improvement paths: re-ranking, better embeddings (BAAI/bge), more data per category.

---

## What I'd improve with more time

1. **Authentication** — User login so each customer's order history is tied to their account
2. **Production model** — Use llama-3.3-70b-versatile on a paid tier for reliable multi-parameter tool calling
3. **More agent tools** — Track shipment in real time, process refunds, escalate to human with ticket creation
4. **Re-ranking** — Cross-encoder re-ranking of top-10 retrieved chunks for better accuracy

<!-- ---

## Resume Bullets

```
• Built production-grade RAG + agentic customer support bot; 64.7% retrieval 
  accuracy on 17 held-out test cases; FastAPI backend + Streamlit frontend

• Implemented hybrid LLM routing: intent classifier directs FAQ queries to 
  RAG pipeline and order actions to LangGraph agent with real SQLite tooling

• Designed SQLite session persistence with repository pattern; conversation 
  history survives server restarts and browser reloads via URL query params
```

--- -->
---

*Built with Python 3.12 · FastAPI · ChromaDB · LangGraph · Groq · Streamlit · SQLite*
