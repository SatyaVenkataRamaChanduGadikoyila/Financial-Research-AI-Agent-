import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq

api_key = os.getenv("GROQ_API_KEY")
print("API Key prefix:", api_key[:10] if api_key else None)

try:
    llm = ChatGroq(
        api_key=api_key,
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=50,
    )
    print("Invoking simple chat...")
    resp = llm.invoke("Hello, are you there?")
    print("Response:", resp.content)
except Exception as e:
    print("Simple call failed:", e)

# Test tool binding
from langchain_core.tools import tool
@tool
def get_dummy_price(ticker: str) -> str:
    """Get stock price."""
    return "100"

try:
    print("Testing tool calling...")
    llm_with_tools = llm.bind_tools([get_dummy_price])
    resp = llm_with_tools.invoke("What is the price of RELIANCE?")
    print("Tool call response tool_calls:", resp.tool_calls)
    print("Tool call response content:", resp.content)
except Exception as e:
    print("Tool call failed:", e)
