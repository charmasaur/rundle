from dataclasses import dataclass
from datetime import datetime, date
from functools import lru_cache
import hashlib
import os
import random
import uuid

import pytz
from flask import render_template, Markup, request, url_for
from flask_sqlalchemy import SQLAlchemy
from geographiclib.geodesic import Geodesic
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.app import app, db
from app.loader import RundleDay2, create_rundle_day, create_rundle_day_from_key
from app.images import image_data

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
    date = today()

    rundle_day = RundleDay2.query.filter(RundleDay2.date == today()).one_or_none()
    if not rundle_day:
        rundle_day = create_rundle_day(today(), 30)
        db.session.add(rundle_day)
        # Could be a race here, but whatever.
        try:
            db.session.commit()
        except:
            # Could fail due to a race, and uniqueness of date being violated. If so then try to
            # query once more.
            db.session.rollback()
            rundle_day = RundleDay2.query.filter(RundleDay2.date == today()).one()

    return render_rundle_day(rundle_day)

@app.route('/debug', methods=['GET'])
def debug():
    if 'date' in request.args:
        # Pick a new target for the date and render that
        return render_rundle_day(
            create_rundle_day(
                date.fromisoformat(request.args['date']),
                int(request.args.get("lookback", "30")),
            ))
    elif 'past_date' in request.args:
        # Use the run selected on a previous date
        rundle_day = RundleDay2.query.filter(
            RundleDay2.date == date.fromisoformat(request.args['past_date'])).first()
        if not rundle_day:
            return "No day found"
        return render_rundle_day(rundle_day)
    elif 'key' in request.args:
        # Use a specific run
        return render_rundle_day(create_rundle_day_from_key(
            date.fromisoformat("1990-01-01"), int(request.args['key'])))
    else:
        return "Specify date, past_date or key"

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

### Versioning JS

@app.template_filter('version')
@lru_cache
def version(filename):
    h = hashlib.sha1()
    path = f"app{filename}"
    with open(path, "rb") as f:
        h.update(f.read())
    return f"{filename}?v={h.hexdigest()}"
