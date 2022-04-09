import os
import base64

from flask import render_template, Markup

from app.app import app

def path(img):
    root = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(root, 'static', img)

def image_data(svg_text):
    svg_base64 = base64.b64encode(svg_text.encode("ascii")).decode("ascii")
    return f"data:image/svg+xml;base64,{svg_base64}"

DATA = [
]

BEARINGS = [
]
DISTANCES = [
]

def get_ordinal(id):
    for i, data in enumerate(DATA):
        if data["id"] == id:
            return i
    assert False

def dist(target, end):
    return DISTANCES[get_ordinal(target)][get_ordinal(end)]

def bearing(target, end):
    return BEARINGS[get_ordinal(target)][get_ordinal(end)]

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
    target = ""
    return render_template(
        "home.html",
        map=image_data(open(path("")).read()),
        profile=image_data(open(path("")).read()),
        choices= {
                data["name"]: {
                "length": compare(data["d"], DATA[get_ordinal(target)]["d"]),
                "height": compare(data["e"], DATA[get_ordinal(target)]["e"]),
                "distance": dist(target, data["id"]),
                "bearing": bearing(target, data["id"]),
                }
            for data in DATA
            },
        target=DATA[get_ordinal(target)]["name"],
        num_guesses=6,
    )
