"""Initializes the package."""
from flask import Flask
import logging

from . import models
from . import project
from .config import config, set_data_path

__all__ = ['load', 'getProjects', 'getProjectByID', 'listProjects']

# Set logging level to info
logging.basicConfig(level=logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Make certain functions available as package functions
getProjects = project.getProjects
getProjectByID = project.getProjectByID
listProjects = project.listProjects

def load(path):
    """Load a data path for use via Python (instead of as a web server)."""

    set_data_path(path)

    app = Flask(__name__)
    app.config.update({
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(config['dataPathObj'] / 'database' / 'db.sqlite')}",
    })

    models.init_flask_app(app)
    app.app_context().push()

    project.loadProjects()