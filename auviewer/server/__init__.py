"""Initializes the package."""
import logging

# Set logging level to info
logging.basicConfig(level=logging.INFO)

logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)