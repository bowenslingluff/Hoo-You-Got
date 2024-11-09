import sqlite3

import requests
from flask import g, current_app, session, redirect, current_app
from functools import wraps
from datetime import datetime, timedelta, timezone
import re
from config import API_KEY

from config import cache

REGIONS = 'us'
MARKETS = 'h2h'
BOOKMAKERS = 'draftkings'

def connect():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def execute(query, *args):
    db = connect()
    cur = db.execute(query, args)
    db.commit()
    return cur

def query_db(query, args=()):
    cur = connect().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return rv if rv else None

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def get_commenceTimeTo():
    cur_time = datetime.now()
    ret = cur_time + timedelta(hours=168)
    return ret.replace(microsecond=0).isoformat() + 'Z'

def is_after_commence_time(commence_time):
    current_time = datetime.now(timezone.utc).isoformat()
    return current_time > commence_time



def get_upcoming_games(sport):

    # Cache response
    cache_key = f"odds_{sport}"
    cached_response = cache.get(cache_key)
    if cached_response:
        # print(f"Cache hit for {sport}") 
        return cached_response
    
    # print(f"Cache miss for {sport}") 
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/'
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'american',
        'bookmakers': BOOKMAKERS,
        'commenceTimeTo': get_commenceTimeTo()
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []

    games = []
    try:
        odds_data = response.json()
        for game in odds_data:
            if not game.get('bookmakers'):
                continue
                
            bookmaker = next((b for b in game['bookmakers'] if b['key'] == BOOKMAKERS), None)
            if not bookmaker:
                continue

            game_info = {
                'game_id': game['id'],
                'sport': sport,
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'commence_time': format_commence_time(game['commence_time']),
                'odds': extract_odds(bookmaker),
                'live': is_after_commence_time(game['commence_time']),
            }
            games.append(game_info)
        
        cache.set(cache_key, games, timeout=300)
        return games
    except Exception as e:
        print(f"Error processing games: {e}")
        return []


def get_game_details(game_id, sport):
    """Get detailed odds for a specific game"""
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/'
    params = {
        'apiKey': API_KEY,
        'eventIds': game_id,
        'oddsFormat': 'american',
        'bookmakers': BOOKMAKERS
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
    
    games = []
    try:
        odds_data = response.json()
        for game in odds_data:
            if not game.get('bookmakers'):
                continue
                
            bookmaker = next((b for b in game['bookmakers'] 
                            if b['key'] == BOOKMAKERS), None)
            if not bookmaker:
                continue
                
            game_info = {
                'game_id': game_id,
                'sport': sport,
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'commence_time': format_commence_time(game['commence_time']),
                'odds': extract_odds(bookmaker),
                'live': is_after_commence_time(game['commence_time']),
            }
            games.append(game_info)
    except Exception as e:
        print(f"Error processing game data: {e}")
        return []
            
    return games


def get_game_results(game_ids, sport):
    # Fetch game details from API
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/scores/'
    params = {'apiKey': API_KEY,
              'eventIds': game_ids,
              'daysFrom': 3
              }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
    
    

    games = []
    try:
        scores_data = response.json();
        for game in scores_data:  # Since we're querying by game_id, should only be one
            game_info =  {
                'game_id': game['id'],
                'sport': game['sport_key'],
                'commence_time': format_commence_time(game['commence_time']),
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_team_score': int(game['scores'][0]['score']) if game.get('scores') else 0,
                'away_team_score': int(game['scores'][1]['score']) if game.get('scores') else 0,
                'live': is_after_commence_time(game['commence_time']),
                'completed': game.get('completed', False)
            }
            games.append(game_info)

        return games
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error processing game results: {e}")
        return None

def get_bet_result(cur_game, outcome, amount, odds):
    # print("Game :" , cur_game , "Type: " ,  type(cur_game))
    # print("Outcome :" , outcome , "Type: " ,  type(outcome))
    # print("Amount :" , amount , "Type: " ,  type(amount))
    print("Amount :" , odds , "Type: " ,  type(odds))
    # return (result, winnings)
    """Calculate bet result and update database"""
    try:

        chosen_winner = re.sub(r'\s*\([^)]*\)', '', outcome).strip()
        winner = cur_game['home_team'] if cur_game['home_team_score'] > cur_game['away_team_score'] else cur_game['away_team']
        bet_won = winner == chosen_winner
        user_id = session.get("user_id")
        
        # Retrieve current cash balance
        cash = query_db("SELECT cash FROM users WHERE id = ?", (user_id,))
        if not cash:
            raise ValueError("User not found")
        
        cash = float(cash[0]['cash'])
        winnings = calculate_potential_winnings(amount, odds) if bet_won else 0
        # print("Cash :" , cash , "Type: " ,  type(cash))
        # print("Winnings :" , winnings , "Type: " ,  type(winnings))
        # Use database transaction
        try:
            if bet_won:
                new_bal = cash + winnings
                execute("UPDATE users SET cash = ? WHERE id = ?", new_bal, user_id)
            
            result = 1 if bet_won else 0
            execute("UPDATE bets SET result = ? WHERE game_id = ?", result, cur_game['game_id'])
            
            return (result, winnings)
        except Exception as e:
            print(f"Database error: {e}")
            return None
            
    except Exception as e:
        print(f"Error processing bet result: {e}")
        return None

def format_commence_time(commence_time_str):
    """
    Convert UTC timestamp to user-friendly format and adjust for EST timezone
    """
    try:
        # Parse the ISO format timestamp
        commence_time = datetime.strptime(commence_time_str, '%Y-%m-%dT%H:%M:%SZ')
        commence_time -= timedelta(hours=4, minutes=1)
        commence_time_str = commence_time.strftime('%Y-%m-%d %I:%M %p')
        return commence_time_str
    except ValueError as e:
        print(f"Error parsing commence time: {e}")
        return commence_time_str




def extract_odds(bookmaker):
    """
    Extract and format odds from bookmaker data
    Returns a dictionary with team names and their corresponding odds
    """
    try:
        # Find the h2h (moneyline) market
        h2h_market = next((market for market in bookmaker['markets'] 
                          if market['key'] == 'h2h'), None)
        if not h2h_market:
            return None
            
        odds_dict = {}
        for outcome in h2h_market['outcomes']:
            # Format American odds with + sign for positive odds
            price = outcome['price']
            formatted_price = f"+{price}" if price > 0 else str(price)
            odds_dict[outcome['name']] = formatted_price
            
        return odds_dict
    except (KeyError, TypeError) as e:
        print(f"Error extracting odds: {e}")
        return None

def extract_odds_for_outcome(game_details, outcome):
    """
    Extract specific odds for a chosen outcome
    """
    try:
        # Remove any odds information from the outcome string
        team_name = re.sub(r'\s*\([^)]*\)', '', outcome).strip()

        

        print(game_details, team_name, outcome)
        
        # Find the odds in game details
        if 'moneyline' in game_details:
            for team_odds in game_details['moneyline']:
                if team_odds['name'] == team_name:
                    # Convert odds string to numeric value
                    odds = team_odds['price']
                    print(odds)
                    return odds
        
        return None
    except (KeyError, ValueError) as e:
        print(f"Error extracting odds for outcome: {e}")
        return None

def calculate_potential_winnings(amount, odds):
    """
    Calculate potential winnings based on bet amount and American odds
    """
    # print(amount, odds)
    try:
        if odds > 0:
            # Positive odds: (odds/100) * bet amount
            return (odds/100) * amount + amount
        else:
            # Negative odds: (100/|odds|) * bet amount
            return (100/abs(odds)) * amount + amount
    except (TypeError, ZeroDivisionError) as e:
        print(f"Error calculating potential winnings: {e}")
        return None
