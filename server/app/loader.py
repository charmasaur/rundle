from datetime import date
import os
import random
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.app import db

# Record of a single day of Rundle
class RundleDay2(db.Model):
    key = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    target = db.Column(db.String)
    map_image = db.Column(db.LargeBinary) # SVG
    profile_image = db.Column(db.LargeBinary) # SVG
    choices = db.Column(db.JSON) # list of "token", "name", "lat", "lng", "dist" (km), "elev" (m)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]
SHEET_COURSES_RANGE = "Courses!A:F"
SHEET_SEQUENCE_RANGE = "Sequence!A:B"

MAP_IMAGE_FILENAME_PATTERN = "{}_course.svg"
PROFILE_IMAGE_FILENAME_PATTERN = "{}_elev_scaled.svg"

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
        raise ValueError("Not enough data elements")

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
    result = drive.list(spaces='drive', q=f"name contains '{target}'").execute()

    files = result['files']

    if len(files) != 2:
        raise ValueError(f"Incorrect files: {files}")

    file_map = {file['name']: file['id'] for file in files}

    map_image_filename = MAP_IMAGE_FILENAME_PATTERN.format(target)
    profile_image_filename = PROFILE_IMAGE_FILENAME_PATTERN.format(target)

    if map_image_filename not in file_map or profile_image_filename not in file_map:
        raise ValueError(f"Incorrect files: {files}")

    map_image = download_image(drive, file_map[map_image_filename])
    profile_image = download_image(drive, file_map[profile_image_filename])

    day = RundleDay2(
        date=date,
        target=target,
        map_image=map_image,
        profile_image=profile_image,
        choices=choices)

    return day

def download_image(drive, file_id):
    file_resource = drive.get_media(fileId=file_id)
    data = io.BytesIO()
    MediaIoBaseDownload(data, file_resource).next_chunk()
    data.seek(0)
    return data.read()

    # We could get races here and end up with duplicate days in the DB, but it doesn't really
    # matter
    return None
