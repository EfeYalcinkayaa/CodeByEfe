from datetime import datetime
import pytz
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def get_turkey_time():
    return datetime.now(pytz.timezone("Europe/Istanbul"))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    aktif = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_turkey_time)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_turkey_time)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_turkey_time)
