from dataclasses import dataclass
from datetime import datetime, date
from functools import lru_cache
import hashlib
import os
import base64
import random
import uuid

import pytz
from flask import render_template, Markup, request, url_for
from flask_sqlalchemy import SQLAlchemy
from geographiclib.geodesic import Geodesic
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.app import app, db
from app.loader import RundleDay2, load_rundle_day, load_rundle_day_from_token

@dataclass
class Choice:
    name: str
    lat: float
    lng: float
    length: float
    elevation: float

    @staticmethod
    def create(choice):
        return Choice(choice["name"], choice["lat"], choice["lng"], choice["dist"], choice["elev"])

def dist(guess, target):
    return int(Geodesic.WGS84.Inverse(guess.lat, guess.lng, target.lat, target.lng)["s12"] / 1000 + 0.5)

def bearing(guess, target):
    return Geodesic.WGS84.Inverse(guess.lat, guess.lng, target.lat, target.lng)["azi1"]

def image_data(svg_bytes):
    svg_base64 = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{svg_base64}"

def compare(x, y):
    if x < y:
        return -1
    if x == y:
        return 0
    if x > y:
        return 1
    assert False

### Rendering

def today():
    return datetime.now(pytz.timezone("Australia/Sydney")).date()

@app.route('/', methods=['GET'])
def home():
    return render_today();

@app.route('/debug', methods=['GET'])
def debug():
    if 'date' in request.args:
        return render_rundle_day(load_rundle_day(date.fromisoformat(request.args['date'])))
    elif 'token' in request.args:
        return render_rundle_day(load_rundle_day_from_token(
            date.fromisoformat("1990-01-01"), request.args['token']))
    else:
        return render_today()

def render_today():
    rundle_day = RundleDay2.query.filter(RundleDay2.date <= today()).order_by(RundleDay2.date.desc()).first()
    if not rundle_day:
        return "Something went wrong"
    return render_rundle_day(rundle_day)

def render_rundle_day(rundle_day):
    choices = {choice["token"]: Choice.create(choice) for choice in rundle_day.choices}
    target = choices[rundle_day.target]
    return render_template(
        "home.html",
        map=image_data(rundle_day.map_image),
        profile=image_data(rundle_day.profile_image),
        choices={
            choice.name: {
                "length": compare(choice.length, target.length),
                "elevation": compare(choice.elevation, target.elevation),
                "distance": dist(choice, target),
                "bearing": bearing(choice, target),
            }
            for choice in sorted(choices.values(), key=lambda choice: choice.name)
        },
        target=target.name,
        target_details={
            "length": target.length,
            "elevation": target.elevation,
            "lat": target.lat,
            "lng": target.lng,
        },
        num_guesses=6,
        run_date=rundle_day.date.isoformat(),
        mapbox_api_key=os.getenv("MAPBOX_API_KEY", ""),
    )

### Poking

@app.route('/poke', methods=['POST'])
def poke():
    if 'date' in request.args:
        requested_date = date.fromisoformat(request.args['date'])
    else:
        requested_date = today()

    return poke_date(requested_date)

@app.route('/debug/poke', methods=['GET'])
def debugpoke():
    if 'date' in request.args:
        requested_date = date.fromisoformat(request.args['date'])
    else:
        requested_date = today()

    return poke_date(date.fromisoformat(request.args['date']))

def poke_date(requested_date):
    day = RundleDay2.query.filter(RundleDay2.date == requested_date).first()
    if day:
        return f"Already poked for {requested_date}"

    day = load_rundle_day(requested_date)
    db.session.add(day)
    # Could be a race here, but whatever.
    db.session.commit()
    return f"Successfully poked for {requested_date}"

### Versioning JS

@app.template_filter('version')
@lru_cache
def version(filename):
    h = hashlib.sha1()
    path = f"app{filename}"
    with open(path, "rb") as f:
        h.update(f.read())
    return f"{filename}?v={h.hexdigest()}"
