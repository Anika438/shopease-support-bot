import chromadb

TEST_CASES = [
    # ORDER
    {"question": "where is my order", "expected": "ORDER"},
    {"question": "I want to modify my order", "expected": "ORDER"},
    # CANCEL
    {"question": "cancel my order please", "expected": "CANCEL"},
    {"question": "I changed my mind and want to cancel", "expected": "CANCEL"},
    # REFUND
    {"question": "I want my money back", "expected": "REFUND"},
    {"question": "how do I get a refund", "expected": "REFUND"},
    # SHIPPING
    {"question": "my package has not arrived", "expected": "SHIPPING"},
    {"question": "how long does delivery take", "expected": "SHIPPING"},
    # DELIVERY
    {"question": "do you deliver to my country", "expected": "DELIVERY"},
    {"question": "what delivery options do you have", "expected": "DELIVERY"},
    # ACCOUNT
    {"question": "I cannot log into my account", "expected": "ACCOUNT"},
    {"question": "I want to change my account password", "expected": "ACCOUNT"},
    # PAYMENT
    {"question": "my payment did not go through", "expected": "PAYMENT"},
    {"question": "which payment methods do you accept", "expected": "PAYMENT"},
    # INVOICE
    {"question": "I need a copy of my invoice", "expected": "INVOICE"},
    # CONTACT
    {"question": "how do I contact customer support", "expected": "CONTACT"},
    # FEEDBACK
    {"question": "I want to leave a review", "expected": "FEEDBACK"},
]

def evaluate():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("support_faqs")
    
    correct = 0
    total = len(TEST_CASES)
    
    print("Running evaluation...\n")

    for tc in TEST_CASES:
      ques=tc["question"]
      exp=tc["expected"]
      results=collection.query(query_texts=[ques],n_results=1)
      category=results["metadatas"][0][0]["category"]
      if(category==exp) :
        print(f"PASS: {tc['question']}")
        correct+=1
      else:
       print(f"FAIL: {tc['question']} → got {category}, expected {tc['expected']}")

    # print final accuracy
    print(f"\nRetrieval accuracy: {correct}/{total} = {correct/total*100:.1f}%")

if __name__ == "__main__":
    evaluate()