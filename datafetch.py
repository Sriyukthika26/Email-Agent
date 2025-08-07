import requests
import json

# Define API URL
url = "https://crm.buildmapper.ai/api/v1/execute_query"

# Set your API key
headers = { "API-Key": "9c77dd4ec15c4c5b8ebd9a83efaeceae", "Content-Type": "application/json"
}

# Define the SQL query (only SELECT queries are allowed)
payload = { "query": "SELECT * FROM crm_team ;"
}
response = requests.post(url, headers=headers, data=json.dumps(payload))

if response.status_code == 200:
    data = response.json()
    # Save the JSON response to a file
    with open('ProdData/crm_team_data.json', 'w') as f:
        json.dump(data, f, indent=2)
else:
    print("❌ Error:", response.status_code, response.text)
