from datetime import date, timedelta
import random

from sqlalchemy import ARRAY

from app.app import db
from app.repository import RundleCourse, create_map_image, create_profile_image

MAX_POINTS = 100

# Record of a single day of Rundle
class RundleDay2(db.Model):
    key = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True)
    target = db.Column(db.String) # string representation of RundleCourse key
    map_image = db.Column(db.LargeBinary) # SVG
    profile_image = db.Column(db.LargeBinary) # SVG
    choices = db.Column(db.JSON) # list of "token", "name", "lat", "lng", "dist" (km), "elev" (m)
    latitudes = db.Column(ARRAY(db.Float), nullable=True)
    longitudes = db.Column(ARRAY(db.Float), nullable=True)


def create_rundle_day(date, lookback):
    """Chooses and creates a RundleDay for the specified date."""
    courses = _load_courses()

    # Try to pick a course that hasn't been used in the last N days
    used = RundleDay2.query.add_columns(
        RundleDay2.date,
        RundleDay2.target,
    ).filter(RundleDay2.date >= date - timedelta(days=lookback)).all()
    used_keys = set(day.target for day in used)

    all_keys = [course.key for course in courses]

    # Choose a random target from the allowed keys.
    allowed_keys = [key for key in all_keys if not str(key) in used_keys]
    if not allowed_keys:
        # Fallback
        allowed_keys = all_keys
    target = random.choice(allowed_keys)

    return _create_rundle_day(date, target, courses)

def create_rundle_day_from_key(date, target):
    """
    Creates a RundleDay for the specified target token, using the specified date as a placeholder
    (but not using it for any choosing).
    """
    return _create_rundle_day(date, target, _load_courses())

def _create_rundle_day(date, target, courses):
    target_course = RundleCourse.query.get(target)

    courses_dicts = [
        {"token": str(course.key),
         "name": course.name,
         "lat": course.lat,
         "lng": course.lng,
         "dist": course.length,
         "elev": course.elevation,
         } for course in courses]

    latitudes = target_course.latitudes or []
    longitudes = target_course.longitudes or []

    if len(latitudes) > MAX_POINTS:
        factor = round(0.5+len(latitudes)/MAX_POINTS)
        latitudes = latitudes[::factor]
        longitudes = longitudes[::factor]

    day = RundleDay2(
        date=date,
        target=str(target_course.key),
        map_image=create_map_image(target_course),
        profile_image=create_profile_image(target_course),
        choices=courses_dicts,
        latitudes=latitudes,
        longitudes=longitudes,
    )

    return day

def _load_courses():
    return RundleCourse.query.add_columns(
        RundleCourse.key,
        RundleCourse.name,
        RundleCourse.approved,
        RundleCourse.length,
        RundleCourse.elevation,
        RundleCourse.lat,
        RundleCourse.lng,
    ).filter(RundleCourse.approved == True).all()
