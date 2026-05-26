import os
import sys
from dotenv import load_dotenv

# Ensure we import app properly
sys.path.insert(0, r'd:\AIProject')
load_dotenv()

import app

print("GROQ_API_KEY in env:", os.environ.get("GROQ_API_KEY")[:10] if os.environ.get("GROQ_API_KEY") else None)

query = "What is the current price of RELIANCE.NS?"
print(f"Running agent with query: {query}")
try:
    response = app.run_agent(query)
    print("\n--- Response ---")
    print(response)
    print("----------------")
except Exception as e:
    print("Agent failed with exception:")
    import traceback
    traceback.print_exc()
