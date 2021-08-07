"""
Holds & provides configuration parameters for auviewer.
"""

import json
import logging
from pathlib import Path

from .shared import createEmptyJSONFile

# Get the code root
# TODO(gus): This may not work when once viewer is pip installable
codeRootPathObj = Path(__file__).resolve().parent

# Read in the built-in default interface templates file. This will (and should)
# # raise an exception if the file does not exist.
with (codeRootPathObj / 'static' / 'builtin_templates' / 'interface_templates.json').open() as f:
    bdit = f.read()

# Read in the built-in default project template file. This will (and should)
# raise an exception if the file does not exist.
with (codeRootPathObj / 'static' / 'builtin_templates' / 'project_template.json').open() as f:
    bdpt = f.read()

# Holds all config params
config = {

    ### General settings

    # TODO: Do we still need this section?



    ### Tuning parameters

    # Max number of data points to transmit for a given view
    'M': 3000,

    # The number to multiply by numDownsamples each time in building downsample
    # levels. For example, if M=3000 and stepMultipler=2, the first downsample
    # is 3K intervals, the second 6K, the third 12K, and so forth.
    'stepMultiplier': 2,



    ### Asset locations

    # AUView code root directory
    'codeRootPathObj': codeRootPathObj,

    # Data directory location (pathlib.Path object).
    # NOTE: This is the only config param that has no default value and must
    # be defined.
    'dataPathObj': None,

    # Path to the projects directory (pathlib.Path object).
    'projectsDirPathObj': None,



    ### Web server configuration

    'host': 'localhost',
    'port': 8001,
    'debug': False,

    # Root directory from which the web application is served. Should begin with a
    # slash and end without a slash (in other words, end with a directory name). If
    # there is no root directory, rootWebPath should be empty string. You must also
    # change the corresponding setting in config.js. Examples:
    # ''
    # '/approot'
    # '/app/root'
    'rootWebPath': '',

    # Password encryption key
    'secret_key': 'THISISADEVELOPMENTSECRETKEY!CHANGEMETONEWRANDOMSTRINGFORPRODUCTION!',

    # Mail integration settings object
    'mail': {},



    ### Templates

    # Built-in default interface templates
    'builtinDefaultInterfaceTemplates': bdit,

    # Built-in default project template
    'builtinDefaultProjectTemplate': bdpt,

    # Global default interface templates (will be overwritten upon a data folder being designated)
    'globalDefaultInterfaceTemplates': "{}",

    # Global default project template (will be overwritten upon a data folder being designated)
    'globalDefaultProjectTemplate': "{}",


}

# Flask configuration object
class FlaskConfigClass(object):
    """ Flask application config """

    # In production, this is needed to build the URL that will be used in
    # Flask-User emails. However, it will also make it so that Flask only serves
    # requests from this hostname. See:
    # https://code.luasoftware.com/tutorials/flask/things-you-should-know-about-flask-server-name/
    # SERVER_NAME = '127.0.0.1'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    CSRF_ENABLED = True

    # Flask-User settings
    USER_APP_NAME = "AUViewer"  # Shown in and email templates and page footers
    USER_ENABLE_CHANGE_USERNAME = False
    USER_ENABLE_CONFIRM_EMAIL = False
    USER_ENABLE_EMAIL = True
    USER_ENABLE_INVITATION = True
    USER_ENABLE_USERNAME = False
    USER_ENABLE_RETYPE_PASSWORD = False
    USER_REQUIRE_INVITATION = True

    # Override default Flask-User URLs with root web path prefix. For documentation,
    # see "URLs" section of https://flask-user.readthedocs.io/en/v0.6/customization.html.
    # These are overridden in serve.py (createApp).
    # USER_CHANGE_PASSWORD_URL = rootWebPath+'/user/change-password'
    # USER_CHANGE_USERNAME_URL = rootWebPath+'/user/change-username'
    # USER_CONFIRM_EMAIL_URL = rootWebPath+'/user/confirm-email/<token>'
    # USER_EMAIL_ACTION_URL = rootWebPath+'/user/email/<id>/<action>'
    # USER_FORGOT_PASSWORD_URL = rootWebPath+'/user/forgot-password'
    # USER_INVITE_URL = rootWebPath+'/user/invite'
    # USER_LOGIN_URL = rootWebPath+'/user/login'
    # USER_LOGOUT_URL = rootWebPath+'/user/logout'
    # USER_MANAGE_EMAILS_URL = rootWebPath+'/user/manage-emails'
    # USER_PROFILE_URL = rootWebPath+'/user/profile'
    # USER_REGISTER_URL = rootWebPath+'/user/register'
    # USER_RESEND_CONFIRM_EMAIL_URL = rootWebPath+'/user/resend-confirm-email'
    # USER_RESET_PASSWORD_URL = rootWebPath+'/user/reset-password/<token>'
    USER_CHANGE_PASSWORD_URL = '/user/change-password'
    USER_CHANGE_USERNAME_URL = '/user/change-username'
    USER_CONFIRM_EMAIL_URL = '/user/confirm-email/<token>'
    USER_EMAIL_ACTION_URL = '/user/email/<id>/<action>'
    USER_FORGOT_PASSWORD_URL = '/user/forgot-password'
    USER_INVITE_URL = '/user/invite'
    USER_LOGIN_URL = '/user/login'
    USER_LOGOUT_URL = '/user/logout'
    USER_MANAGE_EMAILS_URL = '/user/manage-emails'
    USER_PROFILE_URL = '/user/profile'
    USER_REGISTER_URL = '/user/register'
    USER_RESEND_CONFIRM_EMAIL_URL = '/user/resend-confirm-email'
    USER_RESET_PASSWORD_URL = '/user/reset-password/<token>'

    # Override default Flask-User endpoints. For documentation, see "Endpoints"
    # section of https://flask-user.readthedocs.io/en/v0.6/customization.html.
    USER_AFTER_CHANGE_PASSWORD_ENDPOINT = 'index'
    USER_AFTER_CHANGE_USERNAME_ENDPOINT = 'index'
    USER_AFTER_CONFIRM_ENDPOINT = 'index'
    USER_AFTER_FORGOT_PASSWORD_ENDPOINT = 'user.login'
    USER_AFTER_LOGIN_ENDPOINT = 'index'
    USER_AFTER_LOGOUT_ENDPOINT = 'user.login'
    USER_AFTER_REGISTER_ENDPOINT = 'user.login'
    USER_AFTER_RESEND_CONFIRM_EMAIL_ENDPOINT = 'user.login'
    USER_AFTER_RESET_PASSWORD_ENDPOINT = 'user.login'
    USER_INVITE_ENDPOINT = 'index'
    USER_UNCONFIRMED_EMAIL_ENDPOINT = 'user.login'
    USER_UNAUTHENTICATED_ENDPOINT = 'user.login'
    USER_UNAUTHORIZED_ENDPOINT = 'index'

# Load configuration file
def load_config(cp):

    global config

    logging.info(f"Loading config file {cp}.")

    # Unmarshal the config file from JSON into a dict
    with cp.open() as f:
        json_config = json.load(f)

    # The following values are valid and can be pulled from the json config file
    possible_keys = [
        'host',
        'port',
        'debug',

        'rootWebPath',
        'secret_key',
        'mail',
    ]

    # Set/override any valid settings provided in the json config file
    for k in possible_keys:
        if k in json_config:
            config[k] = json_config[k]

# Generate the baseline data directory contents as needed
def scaffold_data_path():

    global config

    # Grab the data folder path object
    p = config['dataPathObj']

    # Scaffold
    (p / 'config').mkdir(exist_ok=True)
    (p / 'database').mkdir(exist_ok=True)
    (p / 'global_templates').mkdir(exist_ok=True)
    (p / 'projects').mkdir(exist_ok=True)
    createEmptyJSONFile(p / 'config' / 'config.json')
    createEmptyJSONFile(p / 'global_templates' / 'interface_templates.json')
    createEmptyJSONFile(p / 'global_templates' / 'project_template.json')

# Sets, prepares, and processes the data path.
def set_data_path(path):

    global config

    # Create a path object, converting a relative path to absolute if necessary
    p = Path(path).resolve()

    # Create the data directory if necessary
    p.mkdir(exist_ok=True)

    # Attach the data path object to config
    config['dataPathObj'] = p

    # Set the project folder path
    config['projectsDirPathObj'] = p / 'projects'

    # Check if a config file is available, and, if so, load the config
    cp = p / 'config' / 'config.json'
    if cp.is_file():
        load_config(cp)

    # Check if global interface templates file is available, and, if so, load it
    gdit = p / 'global_templates' / 'interface_templates.json'
    if gdit.is_file():
        with gdit.open() as f:
            config['globalDefaultInterfaceTemplates'] = f.read()

    # Check if global project template file is available, and, if so, load it
    gdpt = p / 'global_templates' / 'project_template.json'
    if gdpt.is_file():
        with gdpt.open() as f:
            config['globalDefaultProjectTemplate'] = f.read()

    # Set up the data path scaffolding as needed
    scaffold_data_path()