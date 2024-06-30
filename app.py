import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

import helpers

app = Flask(__name__)


conn = sqlite3.connect('bets.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()





@app.route("/")
def index():
    return render_template("index.html")

