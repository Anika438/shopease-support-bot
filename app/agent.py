from langchain.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
import os

from app.database import get_order, update_order_address, update_order_status
from app.rag import retrieve

load_dotenv()

# Tool 1 — check order status
@tool
def check_order_status(order_id: str) -> str:
    """Check the current status and details of a customer order.
    Use this when the customer asks about their order status, 
    where their order is, or wants to know order details.
    Input must be an order ID in format ORD-XXXX (e.g. ORD-1001)."""
    order=get_order(order_id)
    if not order:
        return "Order not found. Please check your order ID."
    return (f"Order ID: {order['order_id']}\n"
            f"Item: {order['item']}\n"
            f"Status: {order['status']}\n"
            f"Address: {order['address']}\n"
            f"Customer: {order['customer_name']}")

# Tool 2 — update shipping address  
@tool
def update_shipping_address(order_id: str, new_address: str) -> str:
    """Update the shipping address for a customer's order.
    Use this when the customer wants to change or update their 
    delivery address. Requires both the order ID and the new address.
    Only works for orders that are still processing or shipped."""
    success = update_order_address(order_id, new_address)
    if success:
      return f"Shipping address for order {order_id} has been updated to: {new_address}"
    return "Failed to update shipping address. Please check your order ID and try again."
  
#Tool 3 — cancel order
@tool
def cancel_order(order_id: str) -> str:
    """Cancel a customer's order.
    Use this when the customer wants to cancel their order.
    Requires the order ID."""
    order=get_order(order_id)
    if not order:
      return "Order not found. Please check your order ID."
    if order['status'] == "delivered" or order['status'] == "cancelled":
        return f"Order {order_id} is already {order['status']} and cannot be cancelled."
    success = update_order_status(order_id, "cancelled")
    if success:
        return f"Order {order_id} has been cancelled."
    return "Failed to cancel order. Please check your order ID and try again."

# #Tool 4 - check knowledge base
# @tool
# def check_knowledge_base(question: str) -> str:
#   """Answer general customer support questions about policies,
#     returns, payments, accounts, and procedures.
#     Use this for any question that doesn't require looking up 
#     a specific order. Input should be the customer's question."""
#   from app.rag import ask
#   answer, sources = ask(question)
#   return answer[:300] if answer else "No information found."

# #Tool 5 - connect to human agent
# @tool
# def escalate_to_human(reason: str) -> str:
#     """Escalate the conversation to a human support agent.
#     Use this when the customer is very frustrated, the issue is 
#     complex, or you cannot resolve it with available tools.
#     Input should be a brief reason for escalation."""
#     return f"I'm sorry that I couldn't resolve your issue. I will connect you to a human support agent who can assist you further. Reason for escalation: {reason}"


tools = [
    check_order_status,
    update_shipping_address,
    cancel_order,
]

system_prompt = """You are Chuggy, a helpful customer support agent for ShopEase.
You have access to tools to check orders, update addresses, and cancel orders.
ALWAYS call the appropriate tool immediately when you have enough information.
Do NOT ask for confirmation before taking action.
Do NOT ask clarifying questions if the order ID and required info are already provided.
If you need an order ID and the customer hasn't provided one, ask for it.
IMPORTANT: If the customer seems frustrated, angry, or their issue cannot be 
resolved with your available tools, respond with empathy and tell them:
'I'm sorry for the inconvenience. I'm connecting you to a human agent who 
can better assist you. Please hold on.' Do NOT use any tool for this."""

def run_agent(question: str, history=None) -> str:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )    
    agent = create_react_agent(llm, tools,prompt=system_prompt)
    chat_history = []
    if history:
        for turn in history:
            if turn['role']=='user':
                chat_history.append(HumanMessage(content=turn['content']))
            else:
                chat_history.append(AIMessage(content=turn['content']))
    chat_history.append(HumanMessage(content=question))
    result=agent.invoke({"messages": chat_history})
    return result["messages"][-1].content
    
if __name__ == "__main__":
    print("Test 1:", run_agent("what is the status of order ORD-1001?"))
    print()
    print("Test 2:", run_agent("please cancel order ORD-1002"))
    print()
    print("Test 3:", run_agent("update shipping address for ORD-1001 to 456 Marine Drive, Mumbai"))
    print()
    print("Test 4:", run_agent("I am very angry nothing is working"))  # should escalate