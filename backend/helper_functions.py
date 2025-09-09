import json, requests
from config import CRM_API_URL, CRM_API_KEY

headers = { "API-Key": CRM_API_KEY, "Content-Type": "application/json" }

def datafetch(query: str)->dict:
    payload = {"query": query}
    response = requests.post(CRM_API_URL, headers=headers, data=json.dumps(payload))
        
    data = response.json()

    records = data["result"]["data"]

    return records
    
def filter_id_fields(data: dict) -> dict:
    """Removes keys from a dictionary that end with 'id'."""
    if not isinstance(data, dict):
        return data
    return {k: v for k, v in data.items() if not k.endswith("id")}