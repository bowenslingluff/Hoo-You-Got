import sqlite3
from flask import g, current_app

def connect():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

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