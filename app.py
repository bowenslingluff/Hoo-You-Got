import os
import requests
import sqlite3
from flask import Flask, g, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

from helpers import connect, execute, close_db, query_db, login_required

app = Flask(__name__)
app.config['DATABASE'] = 'bets.db'


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

API_KEY = '3fe51db060b5849e455f770a4b92b2ab'
REGIONS = 'us'
MARKETS = 'h2h'


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

@app.route("/")
@login_required
def index():
    userid = session.get('userid')

    return render_template("index.html")

@app.route("/baseball")
@login_required
def baseball():
    SPORT = "baseball_mlb"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'american',
    }
    response = requests.get(url, params=params)
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    games = []
    for game in odds_data:
        fanduel_bookmaker = next((bookmaker for bookmaker in game['bookmakers'] if bookmaker['key'] == 'fanduel'), None)
        if fanduel_bookmaker:
            try:
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'moneyline': [
                        {'name': outcome['name'], 'price': outcome['price']}
                        for outcome in fanduel_bookmaker['markets'][0]['outcomes']
                    ]
                }
                games.append(game_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")

    games = games[:5]

    return render_template("baseball.html", games=games)


@app.route("/basketball")
@login_required
def basketball():
    SPORT = "basketball_nba"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'american',
    }
    response = requests.get(url, params=params)
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    games = []
    for game in odds_data:
        fanduel_bookmaker = next((bookmaker for bookmaker in game['bookmakers'] if bookmaker['key'] == 'fanduel'), None)
        if fanduel_bookmaker:
            try:
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'moneyline': [
                        {'name': outcome['name'], 'price': outcome['price']}
                        for outcome in fanduel_bookmaker['markets'][0]['outcomes']
                    ]
                }
                games.append(game_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")

    games = games[:5]

    return render_template("basketball.html", games=games)


@app.route("/football")
@login_required
def football():
    SPORT = "americanfootball_nfl"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'american',
    }
    response = requests.get(url, params=params)
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    games = []
    for game in odds_data:
        fanduel_bookmaker = next((bookmaker for bookmaker in game['bookmakers'] if bookmaker['key'] == 'fanduel'), None)
        if fanduel_bookmaker:
            try:
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'moneyline': [
                        {'name': outcome['name'], 'price': outcome['price']}
                        for outcome in fanduel_bookmaker['markets'][0]['outcomes']
                    ]
                }
                games.append(game_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")

    games = games[:5]

    return render_template("football.html", games=games)


@app.route("/soccer")
@login_required
def soccer():
    SPORT = "soccer_mls"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'american',
    }
    response = requests.get(url, params=params)
    try:
        odds_data = response.json()
    except ValueError:
        print("Error parsing JSON response")
        odds_data = []

    games = []
    for game in odds_data:
        fanduel_bookmaker = next((bookmaker for bookmaker in game['bookmakers'] if bookmaker['key'] == 'fanduel'), None)
        if fanduel_bookmaker:
            try:
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'moneyline': [
                        {'name': outcome['name'], 'price': outcome['price']}
                        for outcome in fanduel_bookmaker['markets'][0]['outcomes']
                    ]
                }
                games.append(game_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")

    games = games[:5]

    return render_template("soccer.html", games=games)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return flash("Enter a username!")

        # Ensure password was submitted
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password:
            flash("All fields are required!")
            return redirect("/register")
        elif not confirmation:
            flash("All fields are required!")
            return redirect("/register")
        elif password != confirmation:
            flash("Passwords do not match!")
            return redirect("/register")

        username = request.form.get("username")
        hash = generate_password_hash(password)

        try:
            execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
            user = query_db("SELECT id FROM users WHERE username = ?", (username,), one=True)
            session["user_id"] = user["id"]
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username must be unique!")
            return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Ensure username was submitted
        if not username or not password:
            return flash("All fields are required!")

        # Query database for username
        rows = query_db(
            "SELECT * FROM users WHERE username = ?", (username,), one=True
        )

        # Ensure username exists and password is correct
        if rows and check_password_hash(rows['hash'], password):
            # Remember which user has logged in
            session["user_id"] = rows["id"]
            # Redirect to the home page
            return redirect("/")
        else:
            flash("Invalid username or password")
            return render_template("login.html")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)