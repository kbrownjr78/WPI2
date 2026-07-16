import os
import sys
import json
from datetime import datetime
import requests

def fetch_schedules():
    """
    Loops through multiple API-Sports subdomains to aggregate daily schedules
    for MLB, NFL, NBA, WNBA, Soccer, and Tennis into a single JSON artifact.
    """
    # 1. Securely retrieve the API key from GitHub Secrets
    api_key = os.environ.get("SPORTS_API_KEY")
    if not api_key:
        print("CRITICAL ERROR: 'SPORTS_API_KEY' environment variable is missing.")
        print("Please configure this variable in your GitHub Repository Settings > Secrets > Actions.")
        sys.exit(1)

       # 2. Define endpoints and hosts for RapidAPI users
    sports_config = {
        "mlb": {
            "url": "https://rapidapi.com",
            "host": "api-baseball.p.rapidapi.com",
            "params": {}
        },
        "nfl": {
            "url": "https://rapidapi.com",
            "host": "api-american-football.p.rapidapi.com",
            "params": {}
        },
        "nba": {
            "url": "https://rapidapi.com",
            "host": "api-basketball.p.rapidapi.com",
            "params": {"league": "12"}  # League ID 12 for NBA
        },
        "wnba": {
            "url": "https://rapidapi.com",
            "host": "api-basketball.p.rapidapi.com",
            "params": {"league": "13"}  # League ID 13 for WNBA
        },
        "soccer": {
            "url": "https://rapidapi.com",
            "host": "api-football-v1.p.rapidapi.com",
            "params": {}
        },
        "tennis": {
            "url": "https://rapidapi.com",
            "host": "api-tennis.p.rapidapi.com",
            "params": {}
        }
    }
    
    # 3. Dynamically compute today's date
    today_date = datetime.today().strftime('%Y-%m-%d')
    print(f"Initializing multi-sport schedule pull for date: {today_date}\n")
    
    # Storage for aggregated results
    master_schedule = {
        "date": today_date,
        "pulled_at": datetime.utcnow().isoformat() + "Z",
        "sports": {}
    }

    # 4. Iterate over each sport configuration
    for sport_name, config in sports_config.items():
        print(f"Fetching data for: {sport_name.upper()}...")
        
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": config["host"]
        }
        
        # Merge basic date parameter with sport-specific query parameters
        query_params = {
            "date": today_date,
            "timezone": "America/New_York"
        }
        query_params.update(config["params"])

        try:
            response = requests.get(config["url"], headers=headers, params=query_params, timeout=15)
            response.raise_for_status() 
            
            data = response.json()
            
            # Check for API-Sports platform validation/subscription errors
            if "errors" in data and data["errors"]:
                print(f"  -> API Error for {sport_name.upper()}: {json.dumps(data['errors'])}")
                master_schedule["sports"][sport_name] = {"error": data["errors"], "games": []}
                continue
            
            # Extract games/fixtures payload
            # Note: Soccer matches are nested under 'response' just like other sports in API-Sports
            games = data.get("response", [])
            print(f"  -> Success: Found {len(games)} matches/games.")
            
            master_schedule["sports"][sport_name] = {
                "results_count": len(games),
                "games": games
            }

        except requests.exceptions.RequestException as e:
            print(f"  -> Connection failed for {sport_name.upper()}: {e}")
            master_schedule["sports"][sport_name] = {"error": str(e), "games": []}

    # 5. Write the combined master schedule payload to the artifact destination
    output_filename = "sports_schedule.json"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(master_schedule, f, indent=4, ensure_ascii=False)
        print(f"\nFinal workflow success: All data consolidated into '{output_filename}'.")
    except IOError as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_schedules()
