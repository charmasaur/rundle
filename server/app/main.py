from dataclasses import dataclass
from datetime import datetime
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
from app.loader import RundleDay, load_rundle_day

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

@app.route('/', methods=['GET'])
def home():
    today = datetime.now(pytz.timezone("Australia/Sydney")).date()

    rundle_day = RundleDay.query.filter(RundleDay.date == today).first()
    if not rundle_day:
        rundle_day = load_rundle_day(today)

    choices = {choice["token"]: Choice.create(choice) for choice in rundle_day.choices}
    target = choices[rundle_day.target]
                                                                                 i
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
        },
        num_guesses=6,
    )
