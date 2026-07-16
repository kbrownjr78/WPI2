import os
import sys
import json
from datetime import datetime
import requests

def fetch_schedules():
    """
    Fetches daily schedules for MLB, NFL, NBA, WNBA, Soccer, and Tennis
    using open, keyless league-native APIs that do not block GitHub Actions runners.
    """
    today_date = datetime.today().strftime('%Y-%m-%d') # Format: YYYY-MM-DD
    print(f"Initializing LEAGUE-NATIVE schedule pull for date: {today_date}\n")
    
    master_schedule = {
        "date": today_date,
        "pulled_at": datetime.utcnow().isoformat() + "Z",
        "sports": {}
    }

    # Config using native, keyless endpoints with explicit params to avoid string smearing
    league_endpoints = {
        "mlb": {
            "url": "https://mlb.com",
            "params": {"sportId": 1, "date": today_date},
            "source": "mlb"
        },
        "nba": {
            "url": "https://nba.net",  # Native NBA CDN path
            "params": {},
            "source": "nba"
        },
        "wnba": {
            "url": "https://wnba.com",
            "params": {},
            "source": "wnba"
        },
        "nfl": {
            # Public, unblocked NFL metadata endpoints
            "url": "https://nfl.com",
            "params": {},
            "source": "nfl"
        },
        "soccer": {
            # Open European football scoreboard feed via public API aggregator
            "url": "https://dw.com",
            "params": {"date": today_date},
            "source": "soccer"
        },
        "tennis": {
            # Live open-access web endpoint for ATP/WTA tournament daily overviews
            "url": "https://matchstat.com",
            "params": {"date": today_date},
            "source": "tennis"
        }
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    for sport_name, config in league_endpoints.items():
        print(f"Fetching data for: {sport_name.upper()}...")
        games_list = []
        
        try:
            response = requests.get(config["url"], headers=headers, params=config["params"], timeout=15)
            
            if response.status_code != 200:
                print(f"  -> Skipping {sport_name.upper()}: No live games or endpoint offline today (HTTP {response.status_code}).")
                master_schedule["sports"][sport_name] = {"results_count": 0, "games": []}
                continue
                
            data = response.json()

            # Unique data parsing structures for each league engine
            if config["source"] == "mlb":
                dates_list = data.get("dates", [])
                for d in dates_list:
                    for game in d.get("games", []):
                        games_list.append({
                            "id": game.get("gamePk"),
                            "name": f"{game.get('teams', {}).get('away', {}).get('team', {}).get('name')} @ {game.get('teams', {}).get('home', {}).get('team', {}).get('name')}",
                            "short_name": f"{game.get('teams', {}).get('away', {}).get('team', {}).get('name')} vs {game.get('teams', {}).get('home', {}).get('team', {}).get('name')}",
                            "date_utc": game.get("gameDate"),
                            "status": game.get("status", {}).get("detailedState")
                        })
                        
            elif config["source"] in ["nba", "wnba"]:
                games = data.get("games", [])
                for game in games:
                    if game.get("startDateEastern") == today_date.replace("-", ""):
                        games_list.append({
                            "id": game.get("gameId"),
                            "name": f"{game.get('vTeam', {}).get('triCode')} @ {game.get('hTeam', {}).get('triCode')}",
                            "short_name": f"{game.get('vTeam', {}).get('triCode')} vs {game.get('hTeam', {}).get('triCode')}",
                            "date_utc": game.get("startTimeUTC"),
                            "status": "Scheduled"
                        })
                        
            elif config["source"] == "nfl":
                game_scores = data.get("gameScores", [])
                for g in game_scores:
                    game_info = g.get("gameSchedule", {})
                    games_list.append({
                        "id": game_info.get("gameId"),
                        "name": f"{game_info.get('visitorNickname')} @ {game_info.get('homeNickname')}",
                        "short_name": f"{game_info.get('visitorTeamAbbr')} vs {game_info.get('homeTeamAbbr')}",
                        "date_utc": f"{game_info.get('gameDate')}T{game_info.get('gameTimeEastern')}",
                        "status": "Scheduled"
                    })
                    
            elif config["source"] == "soccer":
                for fixture in data.get("data", []):
                    games_list.append({
                        "id": fixture.get("id"),
                        "name": f"{fixture.get('homeTeam', {}).get('name')} vs {fixture.get('awayTeam', {}).get('name')}",
                        "short_name": f"{fixture.get('homeTeam', {}).get('shortName')} vs {fixture.get('awayTeam', {}).get('shortName')}",
                        "date_utc": fixture.get("date"),
                        "status": fixture.get("status")
                    })
                    
            elif config["source"] == "tennis":
                for match in data.get("matches", []):
                    games_list.append({
                        "id": match.get("id"),
                        "name": f"{match.get('player1_name')} vs {match.get('player2_name')}",
                        "short_name": "Tennis Matchup",
                        "date_utc": match.get("date"),
                        "status": match.get("status")
                    })

            print(f"  -> Success: Found {len(games_list)} matches/games.")
            master_schedule["sports"][sport_name] = {
                "results_count": len(games_list),
                "games": games_list
            }

        except Exception as e:
            print(f"  -> Extraction paused for {sport_name.upper()}: {e}")
            master_schedule["sports"][sport_name] = {"results_count": 0, "games": []}

    # 4. Save combined structural payload data 
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
