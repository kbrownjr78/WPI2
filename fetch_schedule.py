import os
import sys
import json
from datetime import datetime
import requests

def fetch_schedules():
    """
    Fetches daily match schedules for MLB, NFL, NBA, WNBA, Soccer, and Tennis
    separating URLs and query strings explicitly using dictionary parameters.
    """
    today_date = datetime.today().strftime('%Y-%m-%d') # YYYY-MM-DD
    espn_date = datetime.today().strftime('%Y%m%d')    # YYYYMMDD
    
    print(f"Initializing FREE multi-sport schedule pull for date: {today_date}\n")
    
    master_schedule = {
        "date": today_date,
        "pulled_at": datetime.utcnow().isoformat() + "Z",
        "sports": {}
    }

    # Base endpoints and explicit separate parameters
    free_endpoints = {
        "mlb": {
            "url": "https://espn.com",
            "params": {"dates": espn_date},
            "source": "espn"
        },
        "nfl": {
            "url": "https://espn.com",
            "params": {"dates": espn_date},
            "source": "espn"
        },
        "nba": {
            "url": "https://espn.com",
            "params": {"dates": espn_date},
            "source": "espn"
        },
        "wnba": {
            "url": "https://espn.com",
            "params": {"dates": espn_date},
            "source": "espn"
        },
        "soccer": {
            "url": "https://espn.com",
            "params": {"dates": espn_date},
            "source": "espn"
        },
        "tennis": {
            "url": "https://thesportsdb.com",
            "params": {"d": today_date, "s": "Tennis"},
            "source": "sportsdb"
        }
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for sport_name, config in free_endpoints.items():
        print(f"Fetching data for: {sport_name.upper()}...")
        
        try:
            # Passing params explicitly solves the domain concatenation bug completely
            response = requests.get(config["url"], headers=headers, params=config["params"], timeout=15)
            
            if response.status_code != 200:
                print(f"  -> HTTP Error {response.status_code} for {sport_name.upper()}.")
                master_schedule["sports"][sport_name] = {"games": []}
                continue
                
            data = response.json()
            games_list = []

            if config["source"] == "espn":
                events = data.get("events", [])
                for event in events:
                    games_list.append({
                        "id": event.get("id"),
                        "name": event.get("name"),
                        "short_name": event.get("shortName"),
                        "date_utc": event.get("date"),
                        "status": event.get("status", {}).get("type", {}).get("description")
                    })
            
            elif config["source"] == "sportsdb":
                events = data.get("events", [])
                if events is None:
                    events = []
                for event in events:
                    games_list.append({
                        "id": event.get("idEvent"),
                        "name": event.get("strEvent"),
                        "short_name": f"{event.get('strHomeTeam')} vs {event.get('strAwayTeam')}",
                        "date_utc": f"{event.get('dateEvent')}T{event.get('strTime')}",
                        "status": event.get("strStatus")
                    })

            print(f"  -> Success: Found {len(games_list)} matches/games.")
            master_schedule["sports"][sport_name] = {
                "results_count": len(games_list),
                "games": games_list
            }

        except (ValueError, KeyError) as parse_err:
            print(f"  -> Parsing failed for {sport_name.upper()}: {parse_err}")
            master_schedule["sports"][sport_name] = {"error": "Invalid payload mapping", "games": []}
        except requests.exceptions.RequestException as e:
            print(f"  -> Connection failed for {sport_name.upper()}: {e}")
            master_schedule["sports"][sport_name] = {"error": str(e), "games": []}

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
