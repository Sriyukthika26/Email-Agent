import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

URL = "https://dev.api.buildmapper.ai/odoo/api/v1/companyProfile/projects/fetch/public/id"

# Headers 
HEADERS = {
    "Authorization": os.getenv("API_AUTH"),
    "Content-Type": "application/json",
    "test": "true"
}

def fetch_projects(company_id: int, page: int = 1, limit: int = 5, filters: dict = None):
    payload = {
        "companyId": company_id,
        "page": page,
        "limit": limit,
        "filters": filters or {}
    }

    try:
        response = requests.post(URL, headers=HEADERS, json=payload)

        if response.status_code != 200:
            print("Response text:", response.text)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
