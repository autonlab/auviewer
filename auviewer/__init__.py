"""AUViewer package."""

__VERSION_MAJOR__ = '0'
__VERSION_MINOR__ = '1'
__VERSION_BUILD__ = '1'

__DEBUG = False
if __DEBUG:
    import datetime as dt
    __VERSION_TAGS__ = f"d{dt.datetime.now().strftime('%Y%m%d_%H%M')}"
else:
    __VERSION_TAGS__ = 'rc10'

__VERSION__ = f'{__VERSION_MAJOR__}.{__VERSION_MINOR__}.{__VERSION_BUILD__}{__VERSION_TAGS__}'

# Set logging level to info
import logging
if __DEBUG:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)