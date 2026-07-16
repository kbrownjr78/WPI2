import os
import sys
import json
import requests

def fetch_schedules():
    # Retrieve the API key securely from GitLab CI/CD Variables
    api_key = os.environ.get("SPORTS_API_KEY")
    if not api_key:
        print("Error: SPORTS_API_KEY environment variable is missing.")
        sys.exit(1)

    # Example endpoint using the multi-sport API-Sports platform
    url = "https://api-sports.io"
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    # Query parameters (e.g., fetching today's matches)
    # Adjust live=all, next=10, or date=YYYY-MM-DD based on needs
    params = {"live": "all"} 

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Save the schedule data to an artifact file
        output_filename = "sports_schedule.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully saved schedule data to {output_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Pipeline API request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_schedules()
