import sqlite3

import requests
from flask import g, current_app, session, redirect, request
from functools import wraps
from datetime import datetime, timedelta, timezone
import re
from config import API_KEY


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


def is_pending(last_update):
    last_update_time = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
    current_time = datetime.now(timezone.utc)
    time_48_hours_after = last_update_time + timedelta(hours=48)
    return current_time < time_48_hours_after



def get_upcoming_games(sport):
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
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    games = []
    for game in odds_data:
        if game['bookmakers']:
            bookmaker = game['bookmakers'][0]
            try:
                commence_time_str = get_commence_time(game)

                game_info = {
                    'game_id': game["id"],
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': commence_time_str,
                    'live': is_after_commence_time(game['commence_time']),
                    'moneyline': [
                        {'name': outcome['name'],
                         'price': (str(outcome['price']) if outcome['price'] < 0 else '+' + str(outcome['price']))}
                        for outcome in bookmaker['markets'][0]['outcomes']
                    ]
                }
                games.append(game_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")

    return games


def get_commence_time(game):
    commence_time_str = game['commence_time']
    commence_time = datetime.strptime(commence_time_str, '%Y-%m-%dT%H:%M:%SZ')
    commence_time -= timedelta(hours=4, minutes=1)
    commence_time_str = commence_time.strftime('%Y-%m-%d %I:%M %p')
    return commence_time_str


def get_game_details(game_id, sport):
    # Fetch game details from API
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/'
    params = {'apiKey': API_KEY,
              'eventIds': game_id,
              'oddsFormat': 'american',
              'bookmakers': BOOKMAKERS,
              }
    response = requests.get(url, params=params)
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    games = []
    for game in odds_data:
        if game['bookmakers']:
            bookmaker = game['bookmakers'][0]
            try:
                commence_time_str = get_commence_time(game)
                game_info = {
                    'game_id': game_id,
                    'sport': sport,
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': commence_time_str,
                    'live': is_after_commence_time(game['commence_time']),
                    'moneyline': [
                        {'name': outcome['name'],
                         'price': (str(outcome['price']) if outcome['price'] < 0 else '+' + str(outcome['price']))}
                        for outcome in bookmaker['markets'][0]['outcomes']
                    ]
                }
                games.append(game_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")

    return games


def get_game_results(game_id, sport):
    # Fetch game details from API
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/scores/'
    params = {'apiKey': API_KEY,
              'eventIds': game_id,
              'daysFrom': 3
              }
    response = requests.get(url, params=params)
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    game_info = {}
    for game in odds_data:
        try:
            commence_time_str = get_commence_time(game)
            game_info = {
                'game_id': game['id'],
                'sport': game['sport_key'],
                'commence_time': commence_time_str,
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_team_score': int(game['scores'][0]['score']) if game['scores'] else 0,
                'away_team_score': int(game['scores'][1]['score']) if game['scores'] else 0,
                'pending': is_pending(game['last_update']) if game['last_update'] else is_after_commence_time(game['commence_time']),
                'completed': game['completed']
            }
        except KeyError as e:
            print(f"Missing key in game data: {e}")
        except ValueError as e:
            print(f"Error parsing date: {e}")
    return game_info

def get_bet_result(cur_game, outcome, amount):
    chosen_winner = re.sub(r'\s*\([^)]*\)', '', outcome).strip()

    winner = cur_game['home_team'] if cur_game['home_team_score'] > cur_game['away_team_score'] else cur_game['away_team']
    bet_won = winner == chosen_winner

    print('winner:' + winner + '\n chosen winner:' + chosen_winner + '\n win:' + str(bet_won))

    user_id = session.get("user_id")

    # Retrieve current cash balance
    cash = query_db("SELECT cash FROM users WHERE id = ?", (user_id,))
    cash = float(cash[0]['cash'])

    # Calculate the winnings (only if the bet is won)
    winnings = get_winnings(outcome, amount) if bet_won else 0

    if bet_won:
        # Update the new balance
        new_bal = cash + winnings
        execute("UPDATE users SET cash = ? WHERE id = ?", new_bal, user_id)

        # Update the bet result
        result = 1
        execute("UPDATE bets SET result = ? WHERE game_id = ?", result, cur_game['game_id'])
    else:
        result = 0
        execute("UPDATE bets SET result = ? WHERE game_id = ?", result, cur_game['game_id'])
    return (result, winnings)

def get_winnings(outcome, amount):
    odds = re.search(r'\(([^)]+)\)', outcome).group(1)
    odds = int(odds)

    print('outcome:' + outcome + '\n odds:' + str(odds))
    if odds < 0:
        # Calculate the winnings for negative odds
        winnings = (100 / abs(odds)) * amount
    else:
        # Calculate the winnings for positive odds
        winnings = (odds / 100) * amount

        # Calculate the new balance
    winnings += amount
    return winnings
