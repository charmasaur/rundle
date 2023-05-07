"""
Rundle uploader

Usage: upload.py [--upload] [--url <URL>] [--id <id>]...

--upload     Actually upload data, instead of doing a dry run
--url <URL>  URL to which to send the data [default: http://localhost:5000/create]
--id <id1>   Run ID to upload (empty means all, pass multiple --id arguments to upload multiple)

Options:
  -h --help     Show this screen.
"""
from docopt import docopt


from dataclasses import dataclass
from os.path import exists
import csv
from openpyxl import load_workbook

import requests

@dataclass
class Attributes:
    lat: float
    lng: float
    dist: float
    elev: float


def get_names(reference_filename):
    workbook = load_workbook(reference_filename)
    sheet = workbook.get_sheet_by_name(workbook.get_sheet_names()[0])
    rows = sheet.rows
    # Ignore the header row
    next(rows)
    return {row[0].value: row[1].value for row in rows}

def get_attributes(overview_filename):
    rows = csv.reader(open(overview_filename))
    # Ignore the header row
    next(rows)
    return {
        row[1]: Attributes(
            lat=float(row[2]),
            lng=float(row[3]),
            dist=float(row[4]),
            elev=float(row[5]),
        ) for row in rows}

def generate(upload, url, ids):
    reference_filename = "Rundle/course_reference.xlsx"
    overview_filename = "Rundle/course_overview.csv"
    map_filename_template = "Rundle/course_maps/{}_course.svg"
    profile_filename_template = "Rundle/course_profiles_scaled/{}_elev_scaled.svg"
    gpx_filename_template = "Rundle/course_gpx/{}.gpx"
    gpx_filename_fallback_template = "Rundle/course_gpx/{}.GPX"

    names = get_names(reference_filename)
    attributes = get_attributes(overview_filename)

    if not ids:
        ids = list(names)

    for id in ids:
        map_filename = map_filename_template.format(id)
        profile_filename = profile_filename_template.format(id)
        gpx_filename = gpx_filename_template.format(id)
        if not exists(gpx_filename):
            gpx_filename = gpx_filename_fallback_template.format(id)

        have_data = True
        if not id in attributes:
            print(f"Attributes not found for {id}")
            have_data = False
        if not exists(map_filename):
            print(f"Map '{map_filename}' not found for {id}")
            have_data = False
        if not exists(profile_filename):
            print(f"Profile '{profile_filename}' not found for {id}")
            have_data = False
        if not exists(gpx_filename):
            print(f"GPX '{gpx_filename}' not found for {id}")
            have_data = False

        if not have_data:
            print(f"Ignoring {id}")
            continue

        files = {"gpx": gpx_filename}
        data = {
            "name": names[id],
            "approve": "on",
        }

        if upload:
            print(f"Uploading {id} to {url}")
            r = requests.post(
                url,
                data=data,
                files={key: open(value) for key, value in files.items()},
            )
            if r.status_code == 200:
                print("Success")
            else:
                print(f"Error {r.status_code}: {r.text}")

            continue

        print(f"Would upload {id} with data={data} and files={files} to {url}")

if __name__ == '__main__':
    arguments = docopt(__doc__)
    generate(arguments["--upload"], arguments["--url"], arguments["--id"])
