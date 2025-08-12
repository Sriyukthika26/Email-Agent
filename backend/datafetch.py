import json, requests
from config import CRM_API_URL, CRM_API_KEY

headers = { "API-Key": CRM_API_KEY, "Content-Type": "application/json" }

def datafetch(query: str)->dict:
    payload = {"query": query}
    response = requests.post(CRM_API_URL, headers=headers, data=json.dumps(payload))
        
    data = response.json()

    records = data["result"]["data"]

    return records
