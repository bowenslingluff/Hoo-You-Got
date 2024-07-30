import sqlite3
from flask import g, current_app, session, redirect
from functools import wraps
from datetime import datetime, timedelta

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
    ret = cur_time + timedelta(hours=24)
    return ret.replace(microsecond=0).isoformat() + 'Z'
