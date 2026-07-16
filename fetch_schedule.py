import os
import sys
import json
from datetime import datetime
import requests

def fetch_schedules():
    """
    Consolidates daily schedules for MLB, NFL, NBA, WNBA, Soccer, and Tennis.
    Integrates a custom native parsing loop for MLB, while leveraging resilient
    open-source jsDelivr mirrors for other major sports networks.
    """
    # 1. Compute today's date formats dynamically
    today_date = datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
    espn_date = datetime.today().strftime('%Y%m%d')     # Format: YYYYMMDD
    print(f"Initializing multi-sport schedule pull for date: {today_date}\n")
    
    master_schedule = {
        "date": today_date,
        "pulled_at": datetime.utcnow().isoformat() + "Z",
        "sports": {}
    }

    # Standard browser headers to prevent WAF / CDN request blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    # --- SECTION A: INTEGRATED CUSTOM MLB LOOKUP ---
    print("Fetching data for: MLB...")
    mlb_url = "https://mlb.com"
    mlb_params = {"sportId": 1, "date": today_date}
    mlb_games_list = []

    try:
        mlb_response = requests.get(mlb_url, headers=headers, params=mlb_params, timeout=15)
        mlb_response.raise_for_status()
        schedule_data = mlb_response.json()
        
        # Custom Integrated Parsing Loop Structure
        for date_info in schedule_data.get('dates', []):
            print(f" -> Found Game Date: {date_info['date']}")
            for game in date_info.get('games', []):
                away_team = game['teams']['away']['team']['name']
                home_team = game['teams']['home']['team']['name']
                print(f"    - {away_team} @ {home_team}")
                
                # Append cleaned payload data to global array
                mlb_games_list.append({
                    "id": game.get("gamePk"),
                    "name": f"{away_team} @ {home_team}",
                    "short_name": f"{away_team} vs {home_team}",
                    "date_utc": game.get("gameDate"),
                    "status": game.get("status", {}).get("detailedState", "Scheduled")
                })
        
        master_schedule["sports"]["mlb"] = {
            "results_count": len(mlb_games_list),
            "games": mlb_games_list
        }
        print(f"  -> Success: Found {len(mlb_games_list)} MLB games.\n")
    except Exception as e:
        print(f"  -> MLB Extraction error: {e}\n")
        master_schedule["sports"]["mlb"] = {"results_count": 0, "games": []}


    # --- SECTION B: ALL OTHER SPORTS (CDN FALLBACKS) ---
    other_sports_paths = {
        "nfl": f"https://jsdelivr.net{espn_date}_scoreboard.json",
        "nba": f"https://jsdelivr.net{espn_date}_scoreboard.json",
        "wnba": f"https://jsdelivr.net{espn_date}_scoreboard.json",
        "soccer": f"https://jsdelivr.net{espn_date}_scoreboard.json",
        "tennis": f"https://jsdelivr.net{espn_date}_scoreboard.json"
    }

    for sport_name, target_url in other_sports_paths.items():
        print(f"Fetching data for: {sport_name.upper()}...")
        other_games_list = []
        
        try:
            response = requests.get(target_url, headers=headers, timeout=12)
            
            if response.status_code != 200:
                print(f"  -> No data listed for {sport_name.upper()} today (HTTP {response.status_code}).")
                master_schedule["sports"][sport_name] = {"results_count": 0, "games": []}
                continue
                
            data = response.json()
            events = data.get("events", [])
            
            for event in events:
                other_games_list.append({
                    "id": event.get("id"),
                    "name": event.get("name"),
                    "short_name": event.get("shortName"),
                    "date_utc": event.get("date"),
                    "status": event.get("status", {}).get("type", {}).get("description", "Scheduled")
                })

            print(f"  -> Success: Found {len(other_games_list)} matches/games.")
            master_schedule["sports"][sport_name] = {
                "results_count": len(other_games_list),
                "games": other_games_list
            }

        except Exception as e:
            print(f"  -> Request processing skipped for {sport_name.upper()}: {e}")
            master_schedule["sports"][sport_name] = {"results_count": 0, "games": []}

    # 3. Save combined master payload structure to local repository workspace
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
