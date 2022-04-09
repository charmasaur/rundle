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

def path(img):
    root = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(root, 'static', img)

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
        lat = float(bits[1])
        lng = float(bits[2])
        length = float(bits[3])
        elevation = float(bits[4])
    else:
        name = request.form.get("name")
        if not name:
            return "No name", 400
        lat = request.form.get("lat")
        if not lat:
            return "No latitude", 400
        lng = request.form.get("lng")
        if not lng:
            return "No longitude", 400
        length = request.form.get("length")
        if not length:
            return "No length", 400
        elevation = request.form.get("elevation")
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
