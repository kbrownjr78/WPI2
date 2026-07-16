import json
import os
import requests

# Dictionary mapping local file names to hidden ESPN core API endpoints
SPORTS_ENDPOINTS = {
    "nfl": "https://espn.com",
    "nba": "https://espn.com",
    "mlb": "https://espn.com",
    "nhl": "https://espn.com",
    "soccer_epl": "https://espn.com"
}

def fetch_and_save_schedule():
    # Ensure target directory exists
    os.makedirs("data", exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for sport, url in SPORTS_ENDPOINTS.items():
        print(f"Fetching current schedule data for: {sport.upper()}...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Save beautifully formatted JSON
                file_path = f"data/{sport}_schedule.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Successfully saved {file_path}")
            else:
                print(f"Failed to fetch {sport}: HTTP Status {response.status_code}")
                
        except Exception as e:
            print(f"An error occurred while processing {sport}: {str(e)}")

if __name__ == "__main__":
    fetch_and_save_schedule()
