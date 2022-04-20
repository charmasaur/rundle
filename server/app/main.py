import os
import base64
import random
import uuid

from flask import render_template, Markup, request, url_for
from flask_sqlalchemy import SQLAlchemy
from geographiclib.geodesic import Geodesic

from app.app import app, db

class Run(db.Model):
    __tablename__ = "run"

    token = db.Column(db.String, primary_key=True)
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
                "token": run.token,
                "name": run.name,
                "length": run.length,
                "elevation": run.elevation,
                "latitude": run.lat,
                "longitude": run.lng,
                "url": url_for("view", token=run.token),
            }
            for run in runs
        ],
    )

@app.route('/view/<token>', methods=['GET'])
def view(token):
    if not token:
        return "No token"
    run = Run.query.get(token)
    if not run:
        return "Run not found"
    return render_template(
        "view.html",
        map=image_data(run.map_image),
        profile=image_data(run.profile_image),
        token=run.token,
        name=run.name,
        length=run.length,
        elevation=run.elevation,
        latitude=run.lat,
        longitude=run.lng,
        delete_url=url_for("delete", token=run.token),
    )

@app.route('/delete/<token>', methods=['GET'])
def delete(token):
    if not token:
        return "No token"
    run = Run.query.get(token)
    if not run:
        return "Run not found"
    db.session.delete(run)
    db.session.commit()
    return "Deleted"

@app.route('/create', methods=['GET'])
def create_get():
    return render_template("create.html")

def try_parse_float(x):
    if x is None:
        return None
    try:
        return float(x)
    except ValueError:
        return None

def try_read(x):
    if x is None:
        return None
    return x.read()

@app.route('/create', methods=['POST'])
def create_post():
    token = request.form.get("token")
    if not token:
        return "No token", 400

    name = request.form.get("name")
    if not name:
        return "No name", 400

    lat = try_parse_float(request.form.get("lat"))
    if lat is not None and (lat < -90 or lat > 90):
        return "Invalid latitude", 400
    lng = try_parse_float(request.form.get("lng"))
    if lng is not None and (lng < -180 or lng > 180):
        return "Invalid longitude", 400
    length = try_parse_float(request.form.get("length"))
    elevation = try_parse_float(request.form.get("elevation"))
    map_image = try_read(request.files.get("map_image"))
    profile_image = try_read(request.files.get("profile_image"))
    override = bool(request.form.get("override"))

    # Check for duplicate names
    duplicates = Run.query.filter_by(name=name).all()
    if override and len(duplicates) > 1:
        return "Tried to override but found multiple runs with the same name", 400
    if not override and len(duplicates) > 0:
        return "Duplicate found", 400

    if override and len(duplicates) == 1:
        item = duplicates[0]
        item.token = token
        if name is not None:
            item.name = name
        if lat is not None:
            item.lat = lat
        if lng is not None:
            item.lng = lng
        if length is not None:
            item.length = length
        if elevation is not None:
            item.elevation = elevation
        if map_image is not None:
            item.map_image = map_image
        if profile_image is not None:
            item.profile_image = profile_image

        db.session.commit()
        return "Overrode existing run!"

    # Need all parameters for a new run
    if lat is None:
        return "No latitude", 400
    if lng is None:
        return "No longitude", 400
    if length is None:
        return "No length", 400
    if elevation is None:
        return "No elevation", 400
    if map_image is None:
        return "No map image", 400
    if profile_image is None:
        return "No elevation profile image", 400

    item = Run(
        token=token,
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
    return "Created new run!"
