import requests
import json
import os

# Switch environment: "dev" or "staging"
ENV = "staging"
BASE_URL = f"https://{ENV}.api.buildmapper.ai"
ENDPOINT = "/odoo/api/v1/companyProfile/projects/fetch/public/id"
URL = BASE_URL + ENDPOINT

# Headers
HEADERS = {
    "Authorization": "Basic YnVpbGRNYXBwZXIxMjM0NS1jbGllbnQ6cGFzczEyMzQ1LWNsaWVudA==",
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


if __name__ == "__main__":
    company_id = 163
    result = fetch_projects(company_id)

    if result:
        os.makedirs("ProjectsData", exist_ok=True)
        with open(f'ProjectsData/{company_id}_data.json', 'w') as f:
            json.dump(result["data"]["projects"], f, indent=2)
