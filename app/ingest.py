import urllib.request
import json
import ssl
import certifi
import chromadb
import time

def download_rows(offset, limit):
    url = (
        "https://datasets-server.huggingface.co/rows"
        "?dataset=bitext%2FBitext-customer-support-llm-chatbot-training-dataset"
        f"&config=default&split=train&offset={offset}&limit={limit}"
    )
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx) as response:
        data = json.loads(response.read().decode())
    return data["rows"]

def download_balanced(rows_per_category=50):
    all_rows = []
    print("Sampling across full dataset...")
    for offset in range(0, 26000, 500):
        try:
            rows = download_rows(offset, 100)
            all_rows.extend(rows)
            print(f"  offset {offset}: {len(all_rows)} total so far")
            time.sleep(0.5)  # wait 0.5s between requests
        except Exception as e:
            print(f"  offset {offset}: skipped ({str(e)})")
            time.sleep(2)  # wait longer on error
            continue

        # stop early if we have enough of every category
        by_cat = {}
        for row in all_rows:
            cat = row["row"]["category"]
            by_cat[cat] = by_cat.get(cat, 0) + 1
        if len(by_cat) >= 10 and min(by_cat.values()) >= rows_per_category:
            print(f"\nGot enough rows for all categories. Stopping early.")
            break

    print(f"\nDownloaded {len(all_rows)} rows total")

    by_category = {}
    for row in all_rows:
        cat = row["row"]["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(row)

    print(f"\nFound {len(by_category)} categories:")
    for cat, rows in sorted(by_category.items()):
        print(f"  {cat}: {len(rows)} rows available")

    balanced = []
    for cat, rows in by_category.items():
        balanced.extend(rows[:rows_per_category])

    print(f"\nBalanced sample: {len(balanced)} rows")
    return balanced
# ── ChromaDB setup ─────────────────────────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")
client.delete_collection("support_faqs")  # clear old unbalanced data
collection = client.get_or_create_collection(
    name="support_faqs",
    metadata={"hnsw:space": "cosine"}
)

# ── Ingest balanced data ───────────────────────────────────────
rows = download_balanced(rows_per_category=50)

documents = []
ids = []
metadatas = []

for row in rows:
    r = row["row"]
    idx = row["row_idx"]
    text = f"Q: {r['instruction']}\nA: {r['response']}"
    documents.append(text)
    ids.append(f"faq_{idx}")
    metadatas.append({
        "category": r["category"],
        "intent":   r["intent"],
    })

collection.add(documents=documents, ids=ids, metadatas=metadatas)
print(f"\nDone! {collection.count()} documents stored.")

# ── Sanity check ───────────────────────────────────────────────
def test_query(question):
    results = collection.query(
        query_texts=[question],
        n_results=3
    )
    print(f"\nTop 3 results for '{question}':\n")
    for i, doc in enumerate(results["documents"][0]):
        print(f"Result {i+1}:")
        print(doc[:200])
        print(f"Category: {results['metadatas'][0][i]['category']}")
        print(f"Intent:   {results['metadatas'][0][i]['intent']}")
        print()

test_query("my package hasn't arrived")
test_query("how do I cancel my order?")