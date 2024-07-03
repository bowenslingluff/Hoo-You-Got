import sqlite3
from flask import g, current_app

def connect():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def execute(query, args=(), one=False):
    db = connect()
    cur = db.execute(query, args)
    if query.strip().upper().startswith('SELECT'):
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    else:
        db.commit()
        cur.close()
        return None