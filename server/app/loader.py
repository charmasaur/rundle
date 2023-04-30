from datetime import date
import os
import random
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.app import db

# Record of a single day of Rundle
class RundleDay(db.Model):
    key = db.Column(db.String, primary_key=True)
    date = db.Column(db.Date)
    target = db.Column(db.String)
    map_image = db.Column(db.LargeBinary) # SVG
    profile_image = db.Column(db.LargeBinary) # SVG
    choices = db.Column(db.JSON) # list of "token", "name", "lat", "lng", "dist" (km), "elev" (m)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
]
SHEET_COURSES_RANGE = "Courses!A:F"
SHEET_SEQUENCE_RANGE = "Sequence!A:B"

def load_rundle_day(date):
    creds = service_account.Credentials.from_service_account_file('token.json', scopes=SCOPES)
    
    # Load courses and today's target

    sheet = build('sheets', 'v4', credentials=creds).spreadsheets()
    sheet_id = os.getenv("SHEET_ID", "")
    result = sheet.values().batchGet(
        spreadsheetId=sheet_id,
        ranges=[SHEET_COURSES_RANGE, SHEET_SEQUENCE_RANGE]).execute()
    (
        # courseCode, courseName, lat, lon, dist, elev
        courses_data,
        # date, courseCode
        sequence_data,
    ) = (value_range['values'] for value_range in result['valueRanges'])

    if len(courses_data) < 2:
        raise ValueError("Not enough data")

    sequence_map = {date.fromisoformat(entry[0]): entry[1] for entry in sequence_data[1:]}
    if date in sequence_map:
        target = sequence_map[date]
    else:
        # Uh oh, no specified entry for this date. Use a random course.
        target = random.choice(courses_data[1:])[0]

    choices = [
        {"token": course[0],
         "name": course[1],
         "lat": float(course[2]),
         "lng": float(course[3]),
         "dist": float(course[4]),
         "elev": float(course[5]),
         } for course in courses_data[1:]]

    # Load images

    drive = build('drive', 'v3', credentials=creds).files()

    # TODO: Fetch correct `target` images from Drive


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

    # We could get races here and end up with duplicate days in the DB, but it doesn't really
    # matter
    return None

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

def is_duplicate_name(name, token_to_ignore):
    """Returns true iff the name is already used (ignoring any run with the specified token)."""
    return Run.query.filter(Run.token != token_to_ignore, Run.name == name).count() > 0

@app.route('/create', methods=['POST'])
def create_post():
    token = request.form.get("token")
    if not token:
        return "No token", 400

    name = request.form.get("name")
    if name and is_duplicate_name(name, token):
        return "Duplicate name", 400
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

    existing = Run.query.get(token)
    if existing:
        if not override:
            return "Run already exists", 400

        if name:
            existing.name = name
        if lat is not None:
            existing.lat = lat
        if lng is not None:
            existing.lng = lng
        if length is not None:
            existing.length = length
        if elevation is not None:
            existing.elevation = elevation
        if map_image:
            existing.map_image = map_image
        if profile_image:
            existing.profile_image = profile_image

        db.session.commit()
        return "Overrode existing run!"

    # Need all parameters for a new run
    if not name:
        return "No name", 400
    if lat is None:
        return "No latitude", 400
    if lng is None:
        return "No longitude", 400
    if length is None:
        return "No length", 400
    if elevation is None:
        return "No elevation", 400
    if not map_image:
        return "No map image", 400
    if not profile_image:
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
