import os
import sys
import json
import posixpath
from datetime import datetime
from urllib.parse import urljoin
import requests

def fetch_schedules():
    """
    Fetches daily match schedules for MLB, NFL, NBA, WNBA, Soccer, and Tennis
    using strict URL joining libraries to prevent any string smearing.
    """
    today_date = datetime.today().strftime('%Y-%m-%d')
    espn_date = datetime.today().strftime('%Y%m%d')
    print(f"Initializing FREE multi-sport schedule pull for date: {today_date}\n")
    
    master_schedule = {
        "date": today_date,
        "pulled_at": datetime.utcnow().isoformat() + "Z",
        "sports": {}
    }

    # Strict structure: Base domain URL is completely isolated from the path directories
    cdn_root = "https://jsdelivr.net"
    
    sports_paths = {
        "mlb": f"/gh/sportsdataverse/sportsdataverse-data@main/baseball/mlb/scoreboard/{espn_date}_scoreboard.json",
        "nfl": f"/gh/sportsdataverse/sportsdataverse-data@main/football/nfl/scoreboard/{espn_date}_scoreboard.json",
        "nba": f"/gh/sportsdataverse/sportsdataverse-data@main/basketball/nba/scoreboard/{espn_date}_scoreboard.json",
        "wnba": f"/gh/sportsdataverse/sportsdataverse-data@main/basketball/wnba/scoreboard/{espn_date}_scoreboard.json",
        "soccer": f"/gh/sportsdataverse/sportsdataverse-data@main/soccer/scoreboard/{espn_date}_scoreboard.json",
        "tennis": f"/gh/sportsdataverse/sportsdataverse-data@main/tennis/scoreboard/{espn_date}_scoreboard.json"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    for sport_name, path in sports_paths.items():
        print(f"Fetching data for: {sport_name.upper()}...")
        games_list = []
        
        # Standard urllib urljoin ensures the domain and path are joined flawlessly
        target_url = urljoin(cdn_root, path)
        print(f"  -> Target URL: {target_url}")  # This will print the exact clean URL in GitHub Actions
        
        try:
            response = requests.get(target_url, headers=headers, timeout=12)
            
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
