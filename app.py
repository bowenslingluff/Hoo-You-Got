import os

import sqlite3
from flask import Flask, g, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from config import cache

from helpers import close_db, execute, is_after_commence_time, query_db, login_required, usd, get_commenceTimeTo, \
    get_game_details, get_game_results, get_upcoming_games, get_bet_result, calculate_potential_winnings

app = Flask(__name__)
app.config['DATABASE'] = 'bets.db'

app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

cache.init_app(app)

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

    active_bets = query_db('''
            SELECT b.*, u.cash 
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            WHERE b.user_id = ?
        ''', (user_id,))
    if not active_bets:
        return render_template("index.html", games=[])
    
    sport_games = {}
    for bet in active_bets:
        if bet['sport'] not in sport_games:
            sport_games[bet['sport']] = []
        sport_games[bet['sport']].append(bet['game_id'])

    displaygames = []
    try:
        for sport, game_ids in sport_games.items():
            games = get_game_results(','.join(game_ids), sport)

            if not games:
                continue
                
            for cur_game in games:
                # Print debug information
                # print(f"Current game: {len(games)}")
                # print(f"Current game ID: {cur_game['game_id']}")
                # print(f"Active bets: {len(active_bets)}")
                matching_bets = [bet for bet in active_bets 
                               if bet['game_id'] == cur_game['game_id']]
                if not matching_bets:
                    continue

                for matching_bet in matching_bets:
                    print(matching_bet['id'])
                    bet_info = {
                        'commence_time': cur_game['commence_time'],
                        'home_team': cur_game['home_team'],
                        'away_team': cur_game['away_team'],
                        'home_team_score': cur_game['home_team_score'],
                        'away_team_score': cur_game['away_team_score'],
                        'outcome': matching_bet['outcome'],
                        'odds': matching_bet['odds'],
                        'amount': matching_bet['amount'],
                        'live': cur_game["live"],
                        'completed': cur_game['completed']
                    }

                    result = 0
                    if cur_game['completed']:
                        result_winnings = get_bet_result(cur_game, matching_bet['outcome'], matching_bet['amount'], matching_bet['odds'])
                        # print(result_winnings)

                        if result_winnings is not None:
                            result, winnings = result_winnings
                            bet_info.update({
                                'winnings': winnings,
                                'win': result
                            })

                        execute("""
                            INSERT OR IGNORE INTO past_bets
                            (user_id, game_id, sport, commence_time, home_team, away_team, home_team_score, away_team_score, odds, outcome, amount, winnings, result)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            user_id,
                            matching_bet["game_id"],
                            matching_bet["sport"],
                            bet_info['commence_time'],
                            bet_info['home_team'],
                            bet_info['away_team'],
                            bet_info['home_team_score'],
                            bet_info['away_team_score'],
                            matching_bet['odds'],
                            matching_bet['outcome'],
                            matching_bet['amount'],
                            bet_info['winnings'],
                            bet_info['win']
                        )

                        execute("DELETE FROM bets WHERE id = ?", matching_bet['id'])
                            
                    else:
                        winnings = calculate_potential_winnings(matching_bet['amount'], matching_bet['odds'])
                        bet_info.update({
                                'winnings': winnings,
                                'win': result
                            })

                    if result == 1:
                        winnings = calculate_potential_winnings(matching_bet['amount'], matching_bet['odds'])
                        execute("""
                            UPDATE users 
                            SET cash = cash + ? 
                            WHERE id = ?
                        """, winnings, user_id)

                    displaygames.append(bet_info)
    except ValueError as e:
        print(f"Error parsing date: {e}")
    finally:
        close_db()

    return render_template("index.html", games=displaygames)

@app.route("/past_bets")
@login_required
def past_bets():
    user_id = session.get('user_id')

    rows = query_db("SELECT * FROM past_bets WHERE user_id = ? ", (user_id,))
    games = []
    if rows:
        for row in rows:
            bet_info = {
                'commence_time': row['commence_time'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_team_score': row['home_team_score'],
                'away_team_score': row['away_team_score'],
                'odds': row['odds'],
                'outcome': row['outcome'],
                'amount': row['amount'],
                'winnings': row['winnings'],
                'win': row['result']
            }
            games.append(bet_info)

    return render_template("past_bets.html", games=games)

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
        print(sport)
        return redirect(url_for("bet", game_id=game_id, sport=sport))
    else:
        SPORT = "americanfootball_nfl"
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

    cash = query_db("SELECT cash FROM users WHERE id = ?", (user_id,))
    cash = float(cash[0]["cash"])

    if request.method == "POST":
        amount = float(request.form.get("bet_amount"))
        chosen_team = request.form.get("bet_outcome")
        game_id = request.form.get("game_id")
        sport = request.form.get("sport")

        games = get_game_details(game_id, sport)
        if not games:
            flash("Unable to get game odds. Please try again.")
            return redirect(url_for("bet", game_id=game_id, sport=sport))
            
        game = games[0]
        odds_str = game['odds'].get(chosen_team)
        odds = int(odds_str.replace('+', ''))
        if 1 > amount:
            flash("Must Bet $1. Please try again.")
            return redirect(url_for("bet", game=game))
        elif amount > cash or not amount:
            flash("Balance too low. Please try again.")
            return redirect(url_for("bet", game=game))
        elif not chosen_team:
            flash("Must choose an outcome.")
            return redirect(url_for("bet", game=game))
        
        winnings = calculate_potential_winnings(amount, odds)
        

        # Store bet in the database
        execute("INSERT INTO bets (user_id, game_id, sport, home_team, away_team, commence_time, odds, outcome, amount, potential_winnings) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                user_id, game_id, sport, game["home_team"], game["away_team"], game["commence_time"], odds, chosen_team, amount, winnings)
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
            return redirect("/")
        return render_template("bet.html", game=game, cash=cash)

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
            user = query_db("SELECT id, username FROM users WHERE username = ?", (username,))
            user = user[0]
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
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        rows = rows[0]

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
    rows = query_db("SELECT cash FROM users WHERE id = ?", (userid,))

    if rows:
        rows = rows[0]
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