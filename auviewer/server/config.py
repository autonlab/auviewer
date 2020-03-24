from os import getlogin
import os.path
import json

# This file holds configuration parameters for the medview application.

# Output verbosity
verbose = True

# AUView Data Root
auvDataRoot = None

# A root directory from which the web application is served. Should begin with a
# slash and end without a slask (in other words, end with a directory name). If
# there is no root directory, rootWebPath should be empty string. You must also
# change the corresponding setting in config.js. Examples:
# '/approot'
# '/app/root'
# ''
rootWebPath = ''

# Max number of data points to transmit for a given view
M = 3000

# The number to multiply by numDownsamples each time in building downsample
# levels. For example, if M=3000 and stepMultipler=2, the first downsample
# is 3K intervals, the second 6K, the third 12K, and so forth.
stepMultiplier = 2

# AUView code root directory
auvCodeRoot = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# AUView root data directory should have following structure:
#   [root]
#   - global_templates
#   - - global_default_interface_templates.json (optional)
#   - - global_default_project_template.json (optional)
#   - projects
#   - - [project_name]
#   - - - originals
#   - - - - [original hdf5 files]
#   - - - processed
#   - - - - [empty initially, will be used by AUView to store processed files]
#   - - - templates
#   - - - - project_template.json (optional)
#   - - - - interface_templates.json (optional)

cfg = None

# File locations. Updated in load_config.
projectsDir = 'projects/'
globalTemplatesDir = 'global_templates/'
globalDefaultProjectTemplateFile = 'global_default_project_template.json'
globalDefaultInterfaceTemplatesFile = 'global_default_interface_templates.json'

# Flask application configuration
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
    USER_CHANGE_PASSWORD_URL = rootWebPath+'/user/change-password'
    USER_CHANGE_USERNAME_URL = rootWebPath+'/user/change-username'
    USER_CONFIRM_EMAIL_URL = rootWebPath+'/user/confirm-email/<token>'
    USER_EMAIL_ACTION_URL = rootWebPath+'/user/email/<id>/<action>'
    USER_FORGOT_PASSWORD_URL = rootWebPath+'/user/forgot-password'
    USER_INVITE_URL = rootWebPath+'/user/invite'
    USER_LOGIN_URL = rootWebPath+'/user/login'
    USER_LOGOUT_URL = rootWebPath+'/user/logout'
    USER_MANAGE_EMAILS_URL = rootWebPath+'/user/manage-emails'
    USER_PROFILE_URL = rootWebPath+'/user/profile'
    USER_REGISTER_URL = rootWebPath+'/user/register'
    USER_RESEND_CONFIRM_EMAIL_URL = rootWebPath+'/user/resend-confirm-email'
    USER_RESET_PASSWORD_URL = rootWebPath+'/user/reset-password/<token>'

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

def load_config(fn):
    global cfg
    cfg = json.loads(open(fn, 'r').read())

    global verbose, auvDataRoot, rootWebPath
    verbose = cfg['verbose']
    auvDataRoot = cfg['data_path']
    rootWebPath = cfg['root_web_path']

    global projectsDir, globalTemplatesDir, globalDefaultProjectTemplateFile
    global globalDefaultInterfaceTemplatesFile
    projectsDir = os.path.join(
        auvDataRoot, projectsDir)
    globalTemplatesDir = os.path.join(
        auvDataRoot, globalTemplatesDir)
    globalDefaultProjectTemplateFile = os.path.join(
        globalTemplatesDir, globalDefaultProjectTemplateFile)
    globalDefaultInterfaceTemplatesFile = os.path.join(
        globalTemplatesDir, globalDefaultInterfaceTemplatesFile)

    return cfg
