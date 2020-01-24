from os import getlogin
import os.path

# This file holds configuration parameters for the medview application.

# Output verbosity
verbose = False

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

if getlogin() == 'tracir':
    medFilesDir = '/home/tracir/TRACIR/medfiles/'
else:
    medFilesDir = '/zfsauton/data/public/gwelter/AUView/'

# Original patient data files (which should be preserved and unaltered) go here.
originalsDir = os.path.join(medFilesDir, 'originals/')
# originalsDir = '/Users/gus/Code/medfiles/originals/'

# Processed (i.e. downsampled) patient data files go here.
processedFilesDir = os.path.join(medFilesDir, 'processed/')
# processedFilesDir = '/Users/gus/Code/medfiles/processed/'

# Flask application configuration
class FlaskConfigClass(object):
    """ Flask application config """

    # In production, this is needed to build the URL that will be used in
    # Flask-User emails. However, it will also make it so that Flask only serves
    # requests from this hostname. See:
    # https://code.luasoftware.com/tutorials/flask/things-you-should-know-about-flask-server-name/
    # SERVER_NAME = '127.0.0.1'
    
    # Secret key used for password hashing
    SECRET_KEY = 'THISISADEVELOPMENTSECRETKEY!CHANGEMETONEWRANDOMSTRINGFORPRODUCTION!'
    
    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///userdb.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    CSRF_ENABLED = True

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'fbuqfou29f82012ndnba@gmail.com'
    MAIL_PASSWORD = '[+A1G:%6yQ7g'
    MAIL_DEFAULT_SENDER = '"AUView Medical (noreply)" <fbuqfou29f82012ndnba@gmail.com>'
    
    # Flask-User settings
    USER_APP_NAME = "Auton Universal Viewer - Medical"  # Shown in and email templates and page footers
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
