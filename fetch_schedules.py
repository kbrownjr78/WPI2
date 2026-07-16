import os
import sys
import json
from datetime import datetime
import requests

def fetch_schedules():
    """
    Fetches the current day's sports schedules from an external API
    and saves the raw payload to a JSON file for GitLab artifact retention.
    """
    # 1. Securely retrieve the API key from GitLab CI/CD Variables
    api_key = os.environ.get("SPORTS_API_KEY")
    if not api_key:
        print("CRITICAL ERROR: 'SPORTS_API_KEY' environment variable is missing.")
        print("Please configure this variable in your GitLab Project Settings > CI/CD > Variables.")
        sys.exit(1)

    # 2. Configure target URL and authorization headers
    # Using the sports-focused API-Sports platform as a template
    url = "https://api-sports.io"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    # 3. Dynamically compute today's date for the workflow run
    today_date = datetime.today().strftime('%Y-%m-%d')
    print(f"Initializing schedule pull for date: {today_date}")
    
    # API query parameters
    params = {
        "date": today_date,
        "timezone": "America/New_York"  # Change to your target timezone
    } 

    # 4. Execute the network request with strict error handling
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        # Throws an exception for 4xx or 5xx HTTP status codes
        response.raise_for_status() 
        
        data = response.json()
        
        # Optional validation check to ensure data structures match expectations
        if "response" in data and len(data["response"]) == 0:
            print(f"Warning: API request succeeded, but no sports schedules were returned for {today_date}.")

        # 5. Write the output to a file for the GitLab Artifacts runner to harvest
        output_filename = "sports_schedule.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Success: Today's schedule data successfully saved to '{output_filename}'.")

    except requests.exceptions.Timeout:
        print("ERROR: The request timed out. The sports API server took too long to respond.")
        sys.exit(1)
        
    except requests.exceptions.HTTPError as http_err:
        print(f"ERROR: HTTP error occurred. Status Code: {response.status_code}")
        print(f"Details: {http_err}")
        sys.exit(1)
        
    except requests.exceptions.RequestException as req_err:
        print(f"ERROR: A general network exception occurred while fetching schedules: {req_err}")
        sys.exit(1)
        
    except ValueError:
        print("ERROR: Failed to parse the response payload. The API did not return valid JSON.")
        sys.exit(1)

if __name__ == "__main__":
    fetch_schedules()
