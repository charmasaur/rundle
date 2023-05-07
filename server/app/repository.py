from app.app import db
from sqlalchemy import ARRAY 

class RundleCourse(db.Model):
    key = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    latitudes = db.Column(ARRAY(db.Float))
    longitudes = db.Column(ARRAY(db.Float))
    elevations = db.Column(ARRAY(db.Float))

    # Pre-calculated values, to avoid calculating them for every
    # course every day.
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    distance = db.Column(db.Float)
    elevation = db.Column(db.Float)
