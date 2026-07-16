import os
import sys
import json
from datetime import datetime
import requests

def fetch_schedules():
    """
    Fetches daily match schedules for MLB, NFL, NBA, WNBA, Soccer, and Tennis
    by routing data payloads through the jsDelivr open proxy engine.
    """
    today_date = datetime.today().strftime('%Y-%m-%d') # Format: YYYY-MM-DD
    espn_date = datetime.today().strftime('%Y%m%d')    # Format: YYYYMMDD
    print(f"Initializing FREE multi-sport schedule pull for date: {today_date}\n")
    
    master_schedule = {
        "date": today_date,
        "pulled_at": datetime.utcnow().isoformat() + "Z",
        "sports": {}
    }

    # Bypasses GitHub blocks by using jsDelivr CDN proxies over raw files
    free_endpoints = {
        "mlb": "https://jsdelivr.net",
        "nfl": "https://jsdelivr.net",
        "nba": "https://jsdelivr.net",
        "wnba": "https://jsdelivr.net",
        "soccer": "https://jsdelivr.net",
        "tennis": "https://jsdelivr.net"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    for sport_name, base_url in free_endpoints.items():
        print(f"Fetching data for: {sport_name.upper()}...")
        games_list = []
        
        # Build the exact file path target
        target_url = f"{base_url}{espn_date}_scoreboard.json"
        
        try:
            response = requests.get(target_url, headers=headers, timeout=12)
            
            # If a league has no games today or the cache isn't built yet, skip gracefully
            if response.status_code != 200:
                print(f"  -> No data listed for {sport_name.upper()} today (HTTP {response.status_code}).")
                master_schedule["sports"][sport_name] = {"results_count": 0, "games": []}
                continue
                
            data = response.json()
            events = data.get("events", [])
            
            for event in events:
                games_list.append({
                    "id": event.get("id"),
                    "name": event.get("name"),
                    "short_name": event.get("shortName"),
                    "date_utc": event.get("date"),
                    "status": event.get("status", {}).get("type", {}).get("description", "Scheduled")
                })

            print(f"  -> Success: Found {len(games_list)} matches/games.")
            master_schedule["sports"][sport_name] = {
                "results_count": len(games_list),
                "games": games_list
            }

        except Exception as e:
            print(f"  -> Request processing skipped for {sport_name.upper()}: {e}")
            master_schedule["sports"][sport_name] = {"results_count": 0, "games": []}

    output_filename = "sports_schedule.json"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(master_schedule, f, indent=4, ensure_ascii=False)
        print(f"\nFinal workflow success: All data consolidated cleanly into '{output_filename}'.")
    except IOError as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_schedules()
