"""
Rundle uploader

Usage: upload.py [--upload] [--url <URL>] [--id <id>]...

--upload    Actually upload data, instead of doing a dry run
--url <URL> URL to which to send the data [default: http://localhost:5000/create]
--id <id1>  Run ID to upload (empty means all, pass multiple --id arguments to upload multiple)

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

    names = get_names(reference_filename)
    attributes = get_attributes(overview_filename)

    if not ids:
        ids = list(names)

    for id in ids:
        name = names[id]
        map_filename = map_filename_template.format(id)
        profile_filename = profile_filename_template.format(id)

        assert id in attributes, f"Attributes not found for {id}"
        assert exists(map_filename), f"Map '{map_filename}' not found for {id}"
        assert exists(profile_filename), f"Profile '{profile_filename}' not found for {id}"

        files = {"map_image": map_filename, "profile_image": profile_filename}
        data = {
            "name": name,
            "lat": attributes[id].lat,
            "lng": attributes[id].lng,
            "length": attributes[id].dist,
            "elevation": attributes[id].elev,
            "override": "override",
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
    print(arguments)
    generate(arguments["--upload"], arguments["--url"], arguments["--id"])
