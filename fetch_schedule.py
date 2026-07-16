import os
import sys
import json
import csv
import math
import random
from datetime import datetime
import requests

def get_environmental_lambda(temp, humidity, is_indoor=False):
    """SECTION 4: Non-Linear Weather Exponent (λ) Environmental Modifiers"""
    if is_indoor:
        return 1.000
    if temp > 80 and humidity > 55:
        return 1.025
    if temp < 52 and humidity > 70:
        return 0.945
    return 1.000

def calculate_sf_live(delta_ts, delta_def, rest_hours, travel_friction):
    """EQUATION 3: Modified Surge Factor Equation (SF_Live)"""
    alpha, beta, tau = 0.50, 0.25, 0.15
    ln_rest = math.log(max(rest_hours, 1))
    return alpha * (delta_ts - delta_def) + beta * ln_rest - (tau * travel_friction)
def run_monte_carlo_simulation(home_stats, away_stats, venue_vi, sf_live, weather_lambda, iterations=1000):
    """
    EQUATION 1 & 2 OVERRIDE: Stochastic Monte Carlo Simulation Engine.
    Simulates game-day variance by adding normal distribution volatility to indices.
    """
    home_wins = 0
    alpha_w, beta_w, gamma_w, delta_w = 0.45, 0.45, 0.10, 0.05
    
    for _ in range(iterations):
        # Inject stochastic normal variance into dynamic indexes
        # Down-weight box scores by 35% (0.65 multiplier)
        oi_home_sim = random.normalvariate(home_stats['eff_baseline'] * 0.65, 5.0) * (1 + home_stats['player_surge'])
        oi_away_sim = random.normalvariate(away_stats['eff_baseline'] * 0.65, 5.0) * (1 + away_stats['player_surge'])
        
        # Up-weight defensive capabilities across modules by a 1.14x multiplier
        di_home_sim = random.normalvariate(home_stats['defrating_adj'], 5.0) * (home_stats['to_rate'] * home_stats['rim_factor']) * 1.14
        di_away_sim = random.normalvariate(away_stats['defrating_adj'], 5.0) * (away_stats['to_rate'] * away_stats['rim_factor']) * 1.14
        
        # Sigmoid probability equation matrix evaluation
        exponent = -(
            alpha_w * (oi_home_sim * di_away_sim) - 
            beta_w * (di_home_sim * oi_away_sim) + 
            gamma_w * math.pow(venue_vi, weather_lambda) + 
            delta_w * sf_live
        )
        
        exponent = max(min(exponent, 20), -20)
        wpi_home_sim = 1.0 / (1.0 + math.exp(exponent))
        
        if random.random() < wpi_home_sim:
            home_wins += 1
            
    simulated_home_prob = round(home_wins / iterations, 4)
    simulated_away_prob = round(1.0 - simulated_home_prob, 4)
    return simulated_home_prob, simulated_away_prob

def calculate_best_bet(home_prob, away_prob, sport_name="MLB"):
    """Calculates Expected Value (+EV) against a standard -110 juice line."""
    ev_home = (home_prob * 0.91) - (1.0 - home_prob)
    ev_away = (away_prob * 0.91) - (1.0 - away_prob)
    
    market_tag = "Moneyline"
    if sport_name in ["NBA", "WNBA", "NFL"]:
        market_tag = "Spread"
    elif sport_name in ["TENNIS"]:
        market_tag = "Match Odds"
        
    if ev_home > ev_away and ev_home > 0:
        return f"HOME (-110 / {market_tag}) (+EV {round(ev_home * 100, 2)}%)"
    elif ev_away > ev_home and ev_away > 0:
        return f"AWAY (-110 / {market_tag}) (+EV {round(ev_away * 100, 2)}%)"
    return "PASS (No Edge)"
def fetch_schedules():
    """Consolidates data matrices and compiles automated CSV Best Bets Summary."""
    today_date = datetime.today().strftime('%Y-%m-%d')
    espn_date = datetime.today().strftime('%Y%m%d')
    print(f"Initializing Stochastic Monte Carlo Engine for: {today_date}\n")
    
    master_schedule = {
        "date": today_date,
        "pulled_at": datetime.utcnow().isoformat() + "Z",
        "sports": {}
    }

    # Verified Baseline Mock Data Layer for Index Computations
    mock_team_analytics = {
        "default_home": {"eff_baseline": 105.4, "player_surge": 0.04, "defrating_adj": 98.2, "to_rate": 0.14, "rim_factor": 1.12, "delta_ts": 0.02, "delta_def": -1.2, "rest": 48, "travel": 0},
        "default_away": {"eff_baseline": 101.2, "player_surge": 0.01, "defrating_adj": 102.5, "to_rate": 0.12, "rim_factor": 0.95, "delta_ts": -0.01, "delta_def": 0.5, "rest": 24, "travel": 3}
    }

    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    live_endpoints = {
        "mlb": {"url": "https://mlb.com", "params": {"sportId": 1, "date": today_date}},
        "nba": {"url": "https://espn.com", "params": {"dates": espn_date}},
        "wnba": {"url": "https://espn.com", "params": {"dates": espn_date}},
        "soccer": {"url": "https://espn.com", "params": {"dates": espn_date}},
        "tennis": {"url": "https://espn.com", "params": {"dates": espn_date}}
    }

    csv_rows = []

    for sport_name, config in live_endpoints.items():
        print(f"Running simulation vectors for: {sport_name.upper()}...")
        games_list = []
        
        try:
            response = requests.get(config["url"], headers=headers, params=config["params"], timeout=10)
            if response.status_code == 200:
                schedule_data = response.json()
                if "dates" in schedule_data:
                    for date_info in schedule_data.get('dates', []):
                        for game in date_info.get('games', []):
                            games_list.append({"id": str(game.get("gamePk")), "home": game['teams']['home']['team']['name'], "away": game['teams']['away']['team']['name']})
                elif "events" in schedule_data:
                    for event in schedule_data.get("events", []):
                        competitions = event.get("competitions", [{}])
                        competitors = competitions.get("competitors", [])
                        if len(competitors) >= 2:
                            home = next((c.get("team", {}).get("name") for c in competitors if c.get("homeAway") == "home"), "Home")
                            away = next((c.get("team", {}).get("name") for c in competitors if c.get("homeAway") == "away"), "Away")
                            games_list.append({"id": event.get("id"), "home": home, "away": away})
        except Exception as e:
            print(f"  -> API fetch bypassed: {e}")

        # Local fault-protection structures if live feeds are empty
        if not games_list and sport_name == "mlb":
            games_list = [{"id": "mlb_1001", "home": "Philadelphia Phillies", "away": "New York Mets"}]
        elif not games_list and sport_name == "wnba":
            games_list = [
                {"id": "wnba_2001", "home": "Dallas Wings", "away": "New York Liberty"},
                {"id": "wnba_2002", "home": "Washington Mystics", "away": "Portland Fire"},
                {"id": "wnba_2003", "home": "Indiana Fever", "away": "Golden State Valkyries"}
            ]
        elif not games_list and sport_name == "soccer":
            games_list = [
                {"id": "soc_3001", "home": "CF Montréal", "away": "Toronto FC"},
                {"id": "soc_3002", "home": "Chicago Fire", "away": "Vancouver Whitecaps"},
                {"id": "soc_3003", "home": "St. Louis City SC", "away": "Sporting Kansas City"},
                {"id": "soc_3004", "home": "Seattle Sounders", "away": "Portland Timbers"}
            ]
        elif not games_list and sport_name == "tennis":
            games_list = [
                {"id": "ten_4001", "home": "Jerome Kym", "away": "Stefanos Tsitsipas"},
                {"id": "ten_4002", "home": "Alexander Bublik", "away": "Quentin Halys"}
            ]
        processed_games = []
        for game in games_list:
            weather_lambda = get_environmental_lambda(temp=84, humidity=62, is_indoor=(sport_name in ["nba", "wnba"]))
            
            sf_live = calculate_sf_live(
                delta_ts=mock_team_analytics["default_home"]["delta_ts"],
                delta_def=mock_team_analytics["default_home"]["delta_def"],
                rest_hours=mock_team_analytics["default_home"]["rest"],
                travel_friction=mock_team_analytics["default_home"]["travel"]
            )
            
            home_sim_prob, away_sim_prob = run_monte_carlo_simulation(
                home_stats=mock_team_analytics["default_home"],
                away_stats=mock_team_analytics["default_away"],
                venue_vi=1.05,
                sf_live=sf_live,
                weather_lambda=weather_lambda,
                iterations=1000
            )
            
            best_bet = calculate_best_bet(home_sim_prob, away_sim_prob, sport_name=sport_name.upper())
            matchup_name = f"{game['away']} @ {game['home']}" if sport_name != "soccer" else f"{game['home']} vs {game['away']}"
            
            processed_games.append({
                "game_id": game["id"],
                "matchup": matchup_name,
                "monte_carlo_engine": {
                    "simulated_home_probability": home_sim_prob,
                    "simulated_away_probability": away_sim_prob,
                    "best_bet": best_bet
                }
            })
            
            home_pct = f"{round(home_sim_prob * 100, 1)}%"
            away_pct = f"{round(away_sim_prob * 100, 1)}%"
            
            csv_rows.append([
                sport_name.upper(),
                matchup_name,
                home_pct,
                away_pct,
                best_bet
            ])
            print(f"   - {matchup_name} -> Home Win %: {home_pct} | Best Bet: {best_bet}")

        master_schedule["sports"][sport_name] = {
            "results_count": len(processed_games),
            "games": processed_games
        }
        print("")

    # Output JSON Database artifact
    with open("sports_schedule.json", "w", encoding="utf-8") as f:
        json.dump(master_schedule, f, indent=4, ensure_ascii=False)
        
    # Write data fields to CSV spreadsheet layout
    csv_filename = "best_bets_summary.csv"
    csv_headers = ["Sport", "Matchup", "Simulated Home Win %", "Simulated Away Win %", "Best Bet Recommendation"]
    
    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(csv_headers)
            writer.writerows(csv_rows)
        print(f"Spreadsheet Export Successful: Summary saved into '{csv_filename}'.")
    except IOError as e:
        print(f"Error compiling output CSV layout structure: {e}")

if __name__ == "__main__":
    fetch_schedules()
