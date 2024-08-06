import os


import requests
import sqlite3
from flask import Flask, g, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


from helpers import connect, execute, is_after_commence_time, query_db, login_required, usd, get_commenceTimeTo, get_game_details, get_game_results, get_upcoming_games

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
    user_id = session.get('user_id')
    rows = query_db('SELECT game_id, sport, outcome, amount, result FROM bets WHERE user_id = ?', (user_id,), one=True)
    bets = []
    if rows:
        if isinstance(rows, sqlite3.Row):
            try:
                game_id = rows['game_id']
                sport = rows['sport']
                games = get_game_results(game_id, sport)
                for game in games:

                    bet_info = {
                        'commence_time': game['commence_time'],
                        'outcome': rows['outcome'],
                        'amount': rows['amount'],
                        'live': is_after_commence_time(game['commence_time']),
                        'win': rows['result'],
                        'score': game['scores'],
                        'completed': game['completed']
                    }
                    bets.append(bet_info)
            except KeyError as e:
                print(f"Missing key in game data: {e}")
            except ValueError as e:
                print(f"Error parsing date: {e}")
        else:

            for row in rows:
                try:
                    game_id = row['game_id']
                    sport = row['sport']
                    game = get_game_results(game_id, sport)

                    bet_info = {
                        'commence_time': datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                                '%Y-%m-%d %I:%M %p'),
                        'outcome': row['outcome'],
                        'amount': row['amount'],
                        'live': is_after_commence_time(game['commence_time']),
                        'win': row['result'],
                        'score': game['scores'],
                        'completed': game['completed']
                    }
                    bets.append(bet_info)
                except KeyError as e:
                    print(f"Missing key in game data: {e}")
                except ValueError as e:
                    print(f"Error parsing date: {e}")


    return render_template("index.html", bets=bets)



@app.route("/baseball", methods=["GET", "POST"])
def baseball():
    if request.method == "POST":
        game_id = request.form.get("game_id")
        sport = request.form.get("sport")
        return redirect(url_for("bet", game_id=game_id, sport=sport))
    else:
        SPORT = "baseball_mlb"
        games = get_upcoming_games(SPORT)

        return render_template("baseball.html", games=games)


@app.route("/basketball", methods=["GET", "POST"])
def basketball():
    if request.method == "POST":
        game_id = request.form.get("game_id")
        sport = request.form.get("sport")
        return redirect(url_for("bet", game_id=game_id, sport=sport))
    else:
        SPORT = "basketball_nba"
        games = get_upcoming_games(SPORT)

        return render_template("basketball.html", games=games)


@app.route("/football", methods=["GET", "POST"])
def football():
    if request.method == "POST":
        game_id = request.form.get("game_id")
        sport = request.form.get("sport")
        return redirect(url_for("bet", game_id=game_id, sport=sport))
    else:
        SPORT = "football_nfl"
        games = get_upcoming_games(SPORT)

        return render_template("football.html", games=games)


@app.route("/soccer", methods=["GET", "POST"])
def soccer():
    if request.method == "POST":
        game_id = request.form.get("game_id")
        sport = request.form.get("sport")
        return redirect(url_for("bet", game_id=game_id, sport=sport))
    else:
        SPORT = "soccer_epl"
        games = get_upcoming_games(SPORT)

        return render_template("soccer.html", games=games)

@app.route("/bet", methods=["GET", "POST"])
@login_required
def bet():
    user_id = session.get("user_id")

    cash = query_db("SELECT cash FROM users WHERE id = ?", (user_id,), one=True)
    cash = float(cash["cash"])

    if request.method == "POST":
        amount = float(request.form.get("bet_amount"))
        outcome = request.form.get("bet_outcome")
        game_id = request.form.get("game_id")
        sport = request.form.get("sport")

        if 1 > amount:
            flash("Must Bet $1. Please try again.")
            return redirect(url_for("bet", game_id=game_id, sport=sport))
        elif amount > cash or not amount:
            flash("Balance too low. Please try again.")
            return redirect(url_for("bet", game_id=game_id, sport=sport))
        elif not outcome:
            flash("Must choose an outcome.")
            return redirect(url_for("bet", game_id=game_id, sport=sport))

        # Store bet in the database
        execute("INSERT INTO bets (user_id, game_id, sport, outcome, amount) VALUES (?, ?, ?, ?, ?)",
                user_id, game_id, sport, outcome, amount)
        new_balance = cash - amount
        execute("UPDATE users SET cash = ? WHERE id = ?", new_balance, user_id)

        flash("Bet placed successfully!")
        return redirect("/")
    else:
        game_id = request.args.get("game_id")
        sport = request.args.get("sport")
        # Fetch game details from API
        games = get_game_details(game_id, sport)
        if games:
            game = games[0]
        else:
            flash("Failure to get game details")
            return redirect(url_for("baseball"))
        return render_template("bet.html", game=game, cash=cash, game_id=game_id)

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
            user = query_db("SELECT id, username FROM users WHERE username = ?", (username,), one=True)
            session["user_id"] = user["id"]
            session['username'] = user["username"]
            return redirect(url_for("index"))
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
            flash("All fields are required!")
            return render_template("login.html")

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