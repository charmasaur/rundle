import app.main
import app.repository

from .app import app
from .app import db

# Now that all the models have been imported, create the tables.
db.create_all()
