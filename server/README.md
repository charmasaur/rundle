# Server

The Dockerfile encapsulates the main part of the server. It assumes access to environent variables
`DATABASE_URL` (URL for an external SQL database), `PORT` (port on which the server will run), and
``MAPBOX_API_KEY` (Mapbox API key, obviously).

## Local development

To run locally:
1. Get [Docker Compose](https://docs.docker.com/compose/install/)
1. In this directory run `docker-compose up --build`
1. Navigate to `localhost:5000` in a browser

Edits you make to the code should get picked up the next time you refresh the page.

## Deployment

Deployment happens automatically on merges to main via Render.
