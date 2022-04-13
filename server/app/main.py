import os
import base64
import random
import uuid

from flask import render_template, Markup, request
from flask_sqlalchemy import SQLAlchemy
from geographiclib.geodesic import Geodesic

from app.app import app, db

class Run(db.Model):
    __tablename__ = "run"

    token = db.Column(db.String, default=lambda: uuid.uuid4().hex, primary_key=True)
    name = db.Column(db.String)
    map_image = db.Column(db.LargeBinary) # SVG
    profile_image = db.Column(db.LargeBinary) # SVG
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    length = db.Column(db.Float) # km
    elevation = db.Column(db.Float) # m

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
    runs = Run.query.all()
    if not runs:
        return "No runs yet, sorry"
    target = random.choice(runs)
    return render_template(
        "home.html",
        map=image_data(target.map_image),
        profile=image_data(target.profile_image),
        choices={
            run.name: {
                "length": compare(run.length, target.length),
                "elevation": compare(run.elevation, target.elevation),
                "distance": dist(run, target),
                "bearing": bearing(run, target),
            }
            for run in runs
        },
        target=target.name,
        num_guesses=6,
    )

@app.route('/list', methods=['GET'])
def list():
    runs = Run.query.all()
    return render_template(
        "list.html",
        runs=[
            {
                "name": run.name,
                "length": run.length,
                "elevation": run.elevation,
                "latitude": run.lat,
                "longitude": run.lng,
            }
            for run in runs
        ],
    )

@app.route('/create', methods=['GET'])
def create_get():
    return render_template("create.html")

def try_parse_float(x):
    try:
        return float(x)
    except ValueError:
        return None

@app.route('/create', methods=['POST'])
def create_post():
    alls = request.form.get("all")
    if alls:
        if any(request.form.get(x)
               for x in ["name", "lat", "lng", "length", "elevation"]):
            return "Don't use combined field and individual fields together", 400

        bits = alls.split("|")
        if len(bits) != 5:
            return "Wrong number of parts in combined field", 400

        name = bits[0]
        lat = bits[1]
        lng = bits[2]
        length = bits[3]
        elevation = bits[4]
    else:
        name = request.form.get("name")
        lat = request.form.get("lat")
        lng = request.form.get("lng")
        length = request.form.get("length")
        elevation = request.form.get("elevation")

    if not name:
        return "No name", 400
    lat = try_parse_float(lat)
    if lat is None:
        return "No latitude", 400
    lng = try_parse_float(lng)
    if lng is None:
        return "No longitude", 400
    length = try_parse_float(length)
    if length is None:
        return "No length", 400
    elevation = try_parse_float(elevation)
    if elevation is None:
        return "No elevation", 400

    map_image_file = request.files.get("map_image")
    if not map_image_file:
        return "No map image, 400"
    map_image = map_image_file.read()
    profile_image_file = request.files.get("profile_image")
    if not profile_image_file:
        return "No elevation profile image, 400"
    profile_image = profile_image_file.read()

    if lat < -90 or lat > 90:
        return "Invalid latitude", 400
    if lng < -180 or lng > 180:
        return "Invalid longitude", 400

    # Check for duplicate names
    if Run.query.filter_by(name=name).count():
        return "Duplicate name", 400

    item = Run(
        name=name,
        lat=lat,
        lng=lng,
        length=length,
        elevation=elevation,
        map_image=map_image,
        profile_image=profile_image,
    )
    db.session.add(item)
    db.session.commit()

    return "Success!"
