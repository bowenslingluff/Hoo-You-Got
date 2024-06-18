import re
import sqlite3
from datetime import datetime

from flask import Flask




app = Flask(__name__)
def get_db_connection():
    conn = sqlite3.connect('bets.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return "Hello, Flask!"

