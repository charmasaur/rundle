# Server

The Dockerfile encapsulates the main part of the server. It assumes access to environent variables
`DATABASE_URL` (URL for an external SQL database), `PORT` (port on which the server will run)
and `SHEET_ID` (Google Sheets spreadsheet ID where the data lives), and to a file `token.json` with
the relevant Google Sheets credentials.

## Local development

To run locally:
1. Get [Docker Compose](https://docs.docker.com/compose/install/)
1. In this directory run `docker-compose up --build`
1. Navigate to `localhost:5000` in a browser

Edits you make to the code should get picked up the next time you refresh the page.

## Deployment

Deployment happens automatically on merges to main via Render.

## How does it work?

The architecture is a little weird since I wanted the following:
1. All info about the runs (data, images and sequence) maintained in Google Drive
1. Non-horrible performance
1. Not to implement auth in Rundle

I'm sure there are other ways to achieve those, but here's what I came up with:
1. Sheets/Drive is the source of truth for the data, images and sequence
1. Rundle knows how to pull from Sheets/Drive to get the data it needs for a day (it gets all the
   data, the day's target run, and the images for the day's target run); having Rundle pull means I
   can rely on Sheets/Drive auth
1. That data gets stored as the record for exactly what we did that day (it doesn't get mutated even
   if new runs get added later, or existing runs get edited)
1. Rundle relies on something poking it each day to do the pulling for that day; compared to the
   alternative of doing this pulling lazily the first time somebody needs the data, this approach
   gives less latency for the first user that day (since the pulling is slow), and means that in the
   (somewhat likely) case of an error pulling due to bad data, we can rely on the poker reporting an
   error to me instead of using some kind of alerting API (and if the error doesn't get fixed in
   time Rundle will just fall back to showing the previous day's run)

In practice I've implemented the poker with Apps Script, which can run daily, reports errors to me,
and is already in use for updating the sequence of runs.

Note that, buried in the git history, there's a version that doesn't rely on Sheets/Drive, which was
fully implemented except for auth and the sequence (I thought for a while about a cool way to do it
that wouldn't involve actually writing it in the database, but in the end I think just writing the
sequence is the way to go). It had a UI for listing runs and clicking into them to see details, and
a UI and API for creating runs. I thought it'd be cool (and pretty easy) to add another UI to show
all the runs on a map. Anyway, that version is dead, since (as cool as it was) it was going to be
more awkward to maintain the data, and I didn't want to implement auth.
