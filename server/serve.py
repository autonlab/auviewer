from flask import Flask, Blueprint, send_from_directory, request, render_template, render_template_string
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
#from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from flask_user import confirm_email_required, current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter
from flask_user.signals import user_sent_invitation, user_registered
from project import Project
from file import File
import config
from pprint import pprint
from htmlmin.main import minify

# Simplejson package is required in order to "ignore" NaN values and implicitly
# convert them into null values. RFC JSON spec left out NaN values, even though
# ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the
# Chrome JS engine will throw an error when trying to parse them. Simplejson
# package, with ignore_nan=True, will implicitly convert NaN values into null
# values. Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson as json

def create_app():
    
    project = Project()
    project.processFiles()
    project.loadProcessedFiles()

    # Instantiate the Flask web application class
    app = Flask(__name__, template_folder='../www/templates')
    
    # Make the root web path available for templates
    @app.context_processor
    def inject_dict_for_all_templates():
        return {
            # If root path is empty, set to '/' for the browser
            'rootWebPath': config.rootWebPath or '/'
        }

    # Minify HTML when possible
    @app.after_request
    def response_minify(response):
        if response.content_type == u'text/html; charset=utf-8':
            response.set_data(minify(response.get_data(as_text=True), remove_comments=True))
        return response
    
    # Apply Flask configuration for Flask-User package
    app.config.from_object('config.FlaskConfigClass')

    # Initialize Flask-SQLAlchemy, Flask-Mail, and Flask-Babel
    db = SQLAlchemy(app)
    mail = Mail(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        
        __tablename__ = 'users'
        
        id = db.Column(db.Integer, primary_key=True)
    
        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
        confirmed_at = db.Column(db.DateTime(), nullable=True)
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User information
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
        first_name = db.Column(db.Unicode(50), nullable=False, server_default=u'')
        last_name = db.Column(db.Unicode(50), nullable=False, server_default=u'')

        # Relationships
        roles = db.relationship('Role', secondary='users_roles', backref=db.backref('users', lazy='dynamic'))

    class UserInvitation(db.Model):
        __tablename__ = 'user_invite'
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(255), nullable=False)
        # save the user of the invitee
        invited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
        # token used for registration page to identify user registering
        token = db.Column(db.String(100), nullable=False, server_default='')

    # Define the Role data model
    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), nullable=False, server_default=u'', unique=True)  # for @roles_accepted()

    # Define the UserRoles association model
    class UsersRoles(db.Model):
        __tablename__ = 'users_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    # Create all database tables
    db.create_all()

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(db, User, UserInvitationClass=UserInvitation)  # Select database adapter
    user_manager = UserManager(db_adapter, app)  # Init Flask-User and bind to app

    # You may use the code snippet to create initial/new admin users (since it
    # is not possible through the interface). Alternatively, you could modify
    # the database.
    #
    # new_admin_email = 'gwelter@andrew.cmu.edu'
    # new_admin_pass = 'akeminute'
    # if not User.query.filter(User.email == new_admin_email).first():
    #     u = User(email=new_admin_email, active=True, password=user_manager.hash_password(new_admin_pass))
    #     u.roles.append(Role(name='admin'))
    #     db.session.add(u)
    #     db.session.commit()

    @user_registered.connect_via(app)
    def after_registered_hook(sender, user, user_invite):
        sender.logger.info("USER REGISTERED")

    @user_sent_invitation.connect_via(app)
    def after_invitation_hook(sender, **extra):
        sender.logger.info("USER SENT INVITATION")
    
    # Map our static assets to be served
    app.register_blueprint(Blueprint('css', __name__, static_url_path=config.rootWebPath+'/css', static_folder='../www/css'))
    app.register_blueprint(Blueprint('js', __name__, static_url_path=config.rootWebPath+'/js', static_folder='../www/js'))
    
    ### NON-SECURE AREAS (NO LOGIN REQUIRED) ###
    
    @app.route(config.rootWebPath+'/anyone')
    def home_page():
        return render_template_string("""
            {% extends "base.html" %}
            {% block content %}
                <h2>Home Pages</h2>
                {% if call_or_get(current_user.is_authenticated) %}
                <p><a href="{{ url_for('user.profile') }}">Profile Page</a></p>
                <p><a href="{{ url_for('user.logout') }}">Sign out</a></p>
                {% else %}
                <p><a href="{{ url_for('user.login') }}">Sign in or Register</a></p>
                {% endif %}
            {% endblock %}
            """)

    @app.route(config.rootWebPath+'/user_manage')
    @login_required
    def user_manage():
        pprint(vars(current_user))
        return render_template_string("""
            {% extends "base.html" %}
            {% block content %}
                <h2>Profile Page</h2>
                <p>Hello {{ current_user.email }},</p>
                <p><a href="{{ url_for('home_page') }}">Home Page</a></p>
                <p><a href="{{ url_for('user.change_password') }}">Change password</a></p>
                <p><a href="{{ url_for('user.invite') }}">Invite User</a></p>
                <p><a href="{{ url_for('user.logout') }}">Sign out</a></p>
            {% endblock %}
            """)
    
    ### SECURE AREAS (LOGIN REQUIRED) ###
    
    @app.route(config.rootWebPath+'/')
    @app.route(config.rootWebPath+'/index.html')
    @login_required
    def index():
        #return send_from_directory('../www', 'index.html')
        return render_template('index.html')
    
    @app.route(config.rootWebPath+'/bokeh.html')
    @login_required
    def bokeh():
        return send_from_directory('../www', 'bokeh.html')
    
    @app.route(config.rootWebPath+'/initial_file_payload')
    @login_required
    def initial_file_payload():
    
        if request.method == 'GET' and len(request.args.get('file', default='')) > 0:
    
            # Parse the filename
            filename = request.args.get('file')
    
            # Get the file
            file = project.getFile(filename)
    
            # If we did not find the file, return empty output
            if not isinstance(file, File):
                return ''
    
            # Return the full (zoomed-out but downsampled if appropriate) datasets for
            # all data series.
            output = file.getInitialFilePayload()
            json_output = json.dumps(output, ignore_nan=True)
            
            return json_output
    
        else:
            return "Invalid request."
    
    @app.route(config.rootWebPath+'/all_series_ranged_data', methods=['GET'])
    @login_required
    def all_series_ranged_data():
    
        if request.method == 'GET' and len(request.args.get('file', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:
    
            # Parse the start & stop times
            filename = request.args.get('file')
            start = request.args.get('start', type=float)
            stop = request.args.get('stop', type=float)
    
            # Get the file
            file = project.getFile(filename)
    
            # If we did not find the file, return empty output
            if not isinstance(file, File):
                return ''
    
            output = file.getAllSeriesRangedOutput(start, stop)
            json_output = json.dumps(output, ignore_nan=True)
            
            return json_output
    
        else:
            return "Invalid request."

    @app.route(config.rootWebPath + '/multi_series_ranged_data', methods=['GET'])
    @login_required
    def multi_series_ranged_data():

        if request.method == 'GET' and len(request.args.get('file', default='')) > 0 and len(
                request.args.get('start', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(
                request.args.get('stop', default='')) > 0:

            # Parse the series name and start & stop times
            filename = request.args.get('file')
            series = request.args.getlist('s[]')
            start = request.args.get('start', type=float)
            stop = request.args.get('stop', type=float)

            # Get the file
            file = project.getFile(filename)

            # If we did not find the file, return empty output
            if not isinstance(file, File):
                return ''

            output = file.getMultiSeriesRangedOutput(series, start, stop)
            json_output = json.dumps(output, ignore_nan=True)

            return json_output

    @app.route(config.rootWebPath+'/single_series_ranged_data', methods=['GET'])
    @login_required
    def single_series_ranged_data():
    
        if request.method == 'GET' and len(request.args.get('file', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:
    
            # Parse the series name and start & stop times
            filename = request.args.get('file')
            series = request.args.get('series')
            start = request.args.get('start', type=float)
            stop = request.args.get('stop', type=float)
    
            # Get the file
            file = project.getFile(filename)
    
            # If we did not find the file, return empty output
            if not isinstance(file, File):
                return ''
    
            output = file.getSingleSeriesRangedOutput(series, start, stop)
            json_output = json.dumps(output, ignore_nan=True)
            
            return json_output
        
    @app.route(config.rootWebPath+'/get_alerts', methods=['GET'])
    @login_required
    def get_alerts():
    
        # TODO(gus): Add checks here
        
        # Parse the series name and alert parameters
        filename = request.args.get('file')
        series = request.args.get('series')
        thresholdlow = request.args.get('thresholdlow', type=float)
        thresholdhigh = request.args.get('thresholdhigh', type=float)
        duration = request.args.get('duration', type=float)
        dutycycle = request.args.get('dutycycle', type=float)
        maxgap = request.args.get('maxgap', type=float)
    
        # Generate the mode parameter (see generateThresholdAlerts function
        # description for details on this parameter).
        if request.args.get('thresholdhigh') == '':
            mode = 0
            thresholdhigh = 0
        elif request.args.get('thresholdlow') == '':
            mode = 1
            thresholdlow = 0
        elif request.args.get('thresholdlow') == '' and request.args.get('thresholdhigh') == '':
            # It is invalid for no threshold to be supplied.
            # TODO(gus): Add more generalized parameter checking that covers this,
            # and get rid of this case here.
            return ''
            print("INVALID MODE")
        else:
            mode = 2
    
        # Get the file
        file = project.getFile(filename)
    
        # If we did not find the file, return empty output
        if not isinstance(file, File):
            return ''
    
        output = file.generateAlerts(series, thresholdlow, thresholdhigh, mode, duration, dutycycle, maxgap)
        return json.dumps(output, ignore_nan=True)
    
    @app.route(config.rootWebPath+'/get_annotations', methods=['GET'])
    @login_required
    def get_annotations():
        print("not operational")
    
    @app.route(config.rootWebPath+'/get_files')
    @login_required
    def get_files():
    
        output = project.getActiveFileListOutput()
        return json.dumps(output, ignore_nan=True)
    
    @app.route(config.rootWebPath+'/write_annotation', methods=['GET'])
    @login_required
    def write_annotation():
    
        # Parse parameters
        filename = request.args.get('file')
        xBoundLeft = getFloatParamOrNone('xl')
        xBoundRight = getFloatParamOrNone('xr')
        yBoundTop = getFloatParamOrNone('yt')
        yBoundBottom = getFloatParamOrNone('yb')
        seriesID = request.args.get('sid')
        label = request.args.get('label')
        
        # Get the file
        file = project.getFile(filename)
        
        # If we did not find the file, return empty output
        if not isinstance(file, File):
            print("File could not be retrieved:", filename)
            return ''
        
        # Write the annotation
        file.annotationSet.writeAnnotation(xBoundLeft, xBoundRight, yBoundTop, yBoundBottom, seriesID, label)
        
        return ''
    
    ### HELPERS ###
    
    # Returns the named request parameter as a float or None if the parameter is
    # empty or not present. The default return of None may be overridden.
    def getFloatParamOrNone(name, default=None):
        param = request.args.get(name)
        if param is not None and len(param) > 0:
            return request.args.get(name, type=float)
        else:
            return default
        
    return app

# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8001, debug=True, use_reloader=False)
