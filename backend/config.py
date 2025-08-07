# /config.py
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Securely load API keys from the environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CRM_API_KEY = os.getenv("CRM_API_KEY")

# Set the CRM API endpoint
CRM_API_URL = "https://crm.buildmapper.ai/api/v1/execute_query"

# Set the OpenAI model to be used
LLM_MODEL = "gpt-4o"

# Check for missing API keys at startup
if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
    raise ValueError("OPENAI_API_KEY is not set. Please configure it in your .env file.")

if not CRM_API_KEY:
    raise ValueError("CRM_API_KEY is not set. Please configure it in your .env file.")