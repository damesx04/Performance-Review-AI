import requests

url = "https://api.github.com/search/issues?q=author:damesx04+repo:damesx04/Performance-Review-AI+type:pr&sort=created&order=asc"

try:
    # Make the GET request
    response = requests.get(url)
    response.raise_for_status()  # Raises an error for bad status codes
    
    # Parse the JSON response
    data = response.json()
    
    # Check if 'items' list is not empty and extract the number
    if data.get("items"):
        pr_id = data["items"][0]["number"]
        print(f"Pull Request ID: {pr_id}")
    else:
        print("No pull requests found.")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

#calling sonarqube

# 1. Setup your variables
base_url = "https://sonarcloud.io"  # Replace with your actual SonarQube URL
component_key = "damesx04_Performance-Review-AI"                    # REQUIRED: The key of the project
metric_keys = "cognitive_complexity, duplicated_blocks, sqale_rating, reliability_rating, security_rating, ncloc"     # REQUIRED: Comma-separated list of metrics
pr_id = "1"                                  # Your variable containing the Pull Request ID

# 2. Define the endpoint and parameters
url = f"{base_url}/api/measures/component"

params = {
    "component": component_key,
    "metricKeys": metric_keys,
    "pullRequest": pr_id,       # The parameter name is 'pullRequest'
}

# 3. Make the request
# You may need to add auth=(token, '') if your instance requires login
try:
    response = requests.get(url, params=params)
    response.raise_for_status() # Raises an error for bad responses (4xx, 5xx)
    
    # 4. Handle the response
    data = response.json()
    print("Response Data:", data)

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")