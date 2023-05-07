import io

import gpxpy
import numpy as np
from matplotlib import pyplot as plt
from geographiclib.geodesic import Geodesic

from flask import render_template, redirect, request, url_for
from sqlalchemy import ARRAY 

from app.app import app, db
from app.images import image_data

class RundleCourse(db.Model):
    key = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    latitudes = db.Column(ARRAY(db.Float))
    longitudes = db.Column(ARRAY(db.Float))
    elevations = db.Column(ARRAY(db.Float))

    approved = db.Column(db.Boolean)

    # Pre-calculated values, to avoid calculating them for every
    # course every day.
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    length = db.Column(db.Float) # km
    elevation = db.Column(db.Integer) # m

FIG_SIZE = (4, 4)
MAX_ELEVATION = 2200

def save_to_bytes(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format='svg', bbox_inches='tight')
    buffer.seek(0)
    return buffer.read()

def create_map_image(run):
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.axis('off')
    ax.plot(run.longitudes, run.latitudes, c='r')
    return save_to_bytes(fig)

def create_profile_image(run):
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.axis('off')
    ax.plot(run.elevations, c='k')
    ax.fill_between(np.arange(len(run.elevations)), 0, run.elevations, color='k', alpha=0.2)
    m = min(run.elevations)
    M = max(run.elevations)
    # This is a bit of a hack, but whatever. We try to use a consistent scale, but if this
    # run exceeds the max height of that consistent scale, ignore the scale.
    if M - m <= MAX_ELEVATION:
        ax.set_ylim([m, m + 2200])
    return save_to_bytes(fig)

@app.route('/view/<key>', methods=['GET'])
def view(key):
    if not key:
        return "No key"
    if key == "next":
        run = RundleCourse.query.filter(RundleCourse.approved == False).first()
        if not run:
            return "No more unapproved runs<br>" + format_list_link("Back to list")
    else:
        run = RundleCourse.query.get(int(key))
        if not run:
            return "Run not found"
    return render_template(
        "view.html",
        map=image_data(create_map_image(run)),
        profile=image_data(create_profile_image(run)),
        key=run.key,
        approved=run.approved,
        name=run.name,
        length=run.length,
        elevation=run.elevation,
        latitude=run.lat,
        longitude=run.lng,
        delete_url=url_for("delete", key=run.key),
        update_url=url_for("update", key=run.key),
        list_url=url_for("list_endpoint"),
    )

@app.route('/list', methods=['GET'])
def list_endpoint():
    runs = RundleCourse.query.all()
    run_dicts = [
        {
            "key": str(run.key),
            "name": run.name,
            "approved": run.approved,
            "length": run.length,
            "elevation": run.elevation,
            "latitude": run.lat,
            "longitude": run.lng,
            "url": url_for("view", key=str(run.key)),
        }
        for run in runs]
    return render_template(
        "list.html",
        approved_runs=[r for r in run_dicts if r['approved']],
        unapproved_runs=[r for r in run_dicts if not r['approved']],
    )

@app.route('/delete/<key>', methods=['GET'])
def delete(key):
    if not key:
        return "No key"
    run = RundleCourse.query.get(int(key))
    if not run:
        return "Run not found"
    db.session.delete(run)
    db.session.commit()
    return "Deleted" + "<br>" + format_view_link("next", "View next unapproved")

@app.route('/update/<key>', methods=['POST'])
def update(key):
    if not key:
        return "No key"
    run = RundleCourse.query.get(int(key))
    if not run:
        return "Run not found"
    name = request.form.get("name")
    if name and name != run.name:
        duplicate = find_duplicate(name)
        if duplicate:
            return format_view_link(duplicate.key, "Duplicate name")
        run.name = name

    print(request.form)
    approved = request.form.get("approved")
    run.approved = bool(approved)
    print(run.approved)
    db.session.commit()
    return (
        format_view_link(run.key, "Updated")
        + "<br>"
        + format_view_link("next", "View next unapproved")
        + "<br>"
        + format_list_link("Back to list")
    )

@app.route('/create', methods=['GET'])
def create_get():
    return render_template("create.html")

def find_duplicate(name):
    return RundleCourse.query.filter(RundleCourse.name == name).first()

@app.route('/create', methods=['POST'])
def create_post():
    gpx_file = request.files.get("gpx")
    if not gpx_file:
        return "No GPX", 400

    gpx = gpxpy.parse(gpx_file)
    if not gpx:
        return "Could not open GPX", 400
    if len(gpx.tracks) != 1:
        return f"Expected one track in GPX, got {len(gpx.tracks)}", 400
    track = gpx.tracks[0]
    if len(track.segments) != 1:
        return f"Expected one segment in GPX, got {len(track.segments)}", 400
    segment = gpx.tracks[0].segments[0]
    data = np.array(
        [[point.latitude, point.longitude, point.elevation]
         for point in gpx.tracks[0].segments[0].points])
    elevation = round(np.maximum(0, np.diff(data[:, 2])).sum())
    length = round(
        sum(Geodesic.WGS84.Inverse(*data[i, 0:2], *data[i+1, 0:2])['s12']
            for i in range(len(data)-1)) / 1000,
        1)
    lat, lng = data[0, 0:2]

    name = request.form.get("name")
    if not name:
        name = track.name
        if not name:
            return "No name", 400
    duplicate = find_duplicate(name)
    if duplicate:
        return format_view_link(duplicate.key, "Duplicate name")

    run = RundleCourse(
        name=name,
        latitudes=list(data[:, 0]),
        longitudes=list(data[:, 1]),
        elevations=list(data[:, 2]),
        approved=False,
        lat=lat,
        lng=lng,
        length=length,
        elevation=elevation,
    )
    db.session.add(run)
    db.session.commit()

    return format_view_link(run.key, "Created")

def format_view_link(key, text):
    url = url_for("view", key=str(key))
    return f"<a href='{url}'>{text}</a>"

def format_list_link(text):
    url = url_for("list_endpoint")
    return f"<a href='{url}'>{text}</a>"

