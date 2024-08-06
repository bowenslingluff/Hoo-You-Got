import sqlite3

import requests
from flask import g, current_app, session, redirect, request
from functools import wraps
from datetime import datetime, timedelta, timezone
import pytz

API_KEY = '3fe51db060b5849e455f770a4b92b2ab'
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

def query_db(query, args=(), one=False):
    cur = connect().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

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
    ret = cur_time + timedelta(hours=20)
    return ret.replace(microsecond=0).isoformat() + 'Z'

def is_after_commence_time(commence_time):
    current_time = datetime.now(timezone.utc).isoformat()
    return current_time > commence_time

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
                commence_time_str = game['commence_time']
                commence_time = datetime.strptime(commence_time_str, '%Y-%m-%dT%H:%M:%SZ')
                commence_time -= timedelta(hours=4, minutes=1)
                commence_time_str = commence_time.strftime('%Y-%m-%d %I:%M %p')

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

def get_game_details(game_id, sport):
    print(game_id)
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
                game_info = {
                    'game_id': game_id,
                    'sport': sport,
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %I:%M %p'),
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
              'eventIds': game_id
              }
    response = requests.get(url, params=params)
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    games = []
    for game in odds_data:
        if game['scores']:
            try:
                game_info = {
                    'game_id': game_id,
                    'sport': sport,
                    'scores': {game['scores'][0]['name']: game['scores'][0]['score'],
                               game['scores'][1]['name']: game['scores'][1]['score']}
                }
                games.append(game_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")

    return games