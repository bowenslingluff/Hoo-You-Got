import os
import requests
import sqlite3
from flask import Flask, g, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


from helpers import connect, execute, close_db, query_db, login_required, usd, get_commenceTimeTo

app = Flask(__name__)
app.config['DATABASE'] = 'bets.db'

app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

API_KEY = '3fe51db060b5849e455f770a4b92b2ab'
REGIONS = 'us'
MARKETS = 'h2h'
BOOKMAKERS = 'draftkings'


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
    # userid = session.get('userid')
    # rows = query_db('SELECT game_id, outcome, amount FROM games WHERE userid = ?')

    return render_template("index.html")

@app.route("/place_bet", methods=["POST"])
@login_required
def place_bet():
    game_id = request.form.get("game_id")
    sport = request.form.get("sport")
    return render_template("bet.html", game_id=game_id, sport=sport)

@app.route("/baseball")
def baseball():
    SPORT = "baseball_mlb"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
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
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
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

    return render_template("baseball.html", games=games)


@app.route("/basketball")
def basketball():
    SPORT = "basketball_nba"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
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
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
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


    return render_template("basketball.html", games=games)


@app.route("/football")
def football():
    SPORT = "football_nfl"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
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
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
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


    return render_template("football.html", games=games)


@app.route("/soccer")
def soccer():
    SPORT = "soccer_epl"
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
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
                game_info = {
                    'teams': [game['home_team'], game['away_team']],
                    'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                        '%Y-%m-%d %H:%M:%S'),
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


    return render_template("soccer.html", games=games)

@app.route("/bet", methods=["GET", "POST"])
@login_required
def bet():
    if request.method == "POST":
        user_id = session["user_id"]
        game_id = request.form.get("game_id")
        amount = float(request.form.get("bet_amount"))
        outcome = request.form.get("bet_outcome")

        # Store bet in the database
        execute("INSERT INTO bets (user_id, game_id, outcome, amount) VALUES (?, ?, ?, ?)",
                user_id, game_id, outcome, amount)

        flash("Bet placed successfully!")
        return redirect("/")
    else:
        game_id = request.args.get("game_id")
        sport = request.args.get("sport")

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

        game = []
        for game in odds_data:
            if game['bookmakers']:
                bookmaker = game['bookmakers'][0]
                try:
                    game_info = {
                        'teams': [game['home_team'], game['away_team']],
                        'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                            '%Y-%m-%d %H:%M:%S'),
                        'moneyline': [
                            {'name': outcome['name'],
                             'price': (str(outcome['price']) if outcome['price'] < 0 else '+' + str(outcome['price']))}
                            for outcome in bookmaker['markets'][0]['outcomes']
                        ]
                    }
                    game.append(game_info)
                except KeyError as e:
                    print(f"Missing key in game data: {e}")
                except ValueError as e:
                    print(f"Error parsing date: {e}")

        return render_template("bet.html", game=game)

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
            session['username'] = rows["username"]
            # Redirect to the home page
            return redirect("/")
        else:
            flash("Invalid username or password")
            return render_template("login.html")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/balance")
@login_required
def balance():
    userid = session["user_id"]
    rows = query_db("SELECT cash FROM users WHERE id = ?", (userid,), one=True)
    if rows:
        cash = rows["cash"]

    return render_template("balance.html", cash=cash)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    userid = session["user_id"]
    if request.method == "POST":
        username = session["username"]
        # Ensure password was submitted
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password:
            flash("must provide password")
            return render_template("settings.html", username=username)
        elif not confirmation:
            flash("must provide password")
            return render_template("settings.html", username=username)
        elif password != confirmation:
            flash("must provide password")
            return render_template("settings.html", username=username)

        hash = generate_password_hash(password)

        execute("UPDATE users SET hash =  ? WHERE id = ?", hash, userid)

        flash("Password Changed!")
        return redirect("/")
    else:
        username = session["username"]
        return render_template("settings.html", username=username)

    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)