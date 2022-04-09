from flask import render_template

from app.app import app

@app.route('/', methods=['GET'])
def home():
    return render_template("home.html")
