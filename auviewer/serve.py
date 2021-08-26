from flask import Flask, Blueprint, send_from_directory, request, render_template, render_template_string, abort, Markup
from flask_mail import Mail
from htmlmin.main import minify
from pathlib import Path
from pprint import pprint
import argparse
import logging
import shutil
import tempfile

# Simplejson package is required in order to "ignore" NaN values and implicitly
# convert them into null values. RFC JSON spec left out NaN values, even though
# ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the
# Chrome JS engine will throw an error when trying to parse them. Simplejson
# package, with ignore_nan=True, will implicitly convert NaN values into null
# values. Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson

from . import models
from .api import downsampleFile, getProject, getProjectsPayload, loadProjects
from .patternset import getAssignmentsPayload
from .config import set_data_path, config, FlaskConfigClass

from .flask_user import confirm_email_required, current_user, login_required, UserManager, SQLAlchemyAdapter
from .flask_user.signals import user_sent_invitation, user_registered

def createApp():

    # Instantiate the Flask web application class
    app = Flask(__name__, template_folder=str(config['codeRootPathObj'] / 'static' / 'www' / 'templates'))

    # Auto-reload templates
    app.jinja_env.auto_reload = True

    # Make the root web path available for templates
    @app.context_processor
    def inject_dict_for_all_templates():
        return {
            'rootWebPath': config['rootWebPath']
        }

    # Minify HTML when possible
    @app.after_request
    def response_minify(response):
        if response.content_type == u'text/html; charset=utf-8':
            response.set_data(minify(response.get_data(as_text=True), remove_comments=True))
        return response

    # Apply Flask configuration for Flask-User package
    app.config.from_object(FlaskConfigClass)
    app.config.update({
        'SECRET_KEY': config['secret_key'],
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(config['dataPathObj'] / 'database' / 'db.sqlite')}",
        **config['mail'],
        'USER_CHANGE_PASSWORD_URL': config['rootWebPath'] + app.config['USER_CHANGE_PASSWORD_URL'],
        'USER_CHANGE_USERNAME_URL': config['rootWebPath'] + app.config['USER_CHANGE_USERNAME_URL'],
        'USER_CONFIRM_EMAIL_URL': config['rootWebPath'] + app.config['USER_CONFIRM_EMAIL_URL'],
        'USER_EMAIL_ACTION_URL': config['rootWebPath'] + app.config['USER_EMAIL_ACTION_URL'],
        'USER_FORGOT_PASSWORD_URL': config['rootWebPath'] + app.config['USER_FORGOT_PASSWORD_URL'],
        'USER_INVITE_URL': config['rootWebPath'] + app.config['USER_INVITE_URL'],
        'USER_LOGIN_URL': config['rootWebPath'] + app.config['USER_LOGIN_URL'],
        'USER_LOGOUT_URL': config['rootWebPath'] + app.config['USER_LOGOUT_URL'],
        'USER_MANAGE_EMAILS_URL': config['rootWebPath'] + app.config['USER_MANAGE_EMAILS_URL'],
        'USER_PROFILE_URL': config['rootWebPath'] + app.config['USER_PROFILE_URL'],
        'USER_REGISTER_URL': config['rootWebPath'] + app.config['USER_REGISTER_URL'],
        'USER_RESEND_CONFIRM_EMAIL_URL': config['rootWebPath'] + app.config['USER_RESEND_CONFIRM_EMAIL_URL'],
        'USER_RESET_PASSWORD_URL': config['rootWebPath'] + app.config['USER_RESET_PASSWORD_URL']
    })

    # Initialize the db models with the Flask app
    models.init_flask_app(app)

    # Initialize Flask-Mail
    mail = Mail(app)

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(models.db, models.User, UserInvitationClass=models.UserInvitation)  # Select database adapter
    user_manager = UserManager(db_adapter, app)  # Init Flask-User and bind to app

    # You may use this code snippet below to create initial/new admin users
    # (since it is not possible through the interface). Alternatively, you
    # could modify the database.
    #
    with app.app_context():
        if not models.User.query.first():
            from getpass import getpass
            print("You must create an admin user.")
            fn = input("First name: ")
            ln = input("Last name: ")
            em = input("E-mail: ")
            pw = getpass(prompt="Password: ")
            u = models.User(
                first_name=fn,
                last_name=ln,
                email=em,
                active=True,
                password=user_manager.hash_password(pw),
            )
            u.roles.append(models.Role(name='admin'))
            models.db.session.add(u)
            models.db.session.commit()

    # Load projects
    with app.app_context():
        loadProjects()

    # Instantiate a file for realtime, in-memory usage (probably temporary)
    # TODO(gus): Refactor realtime
    #rtf = File(projparent=None)

    @user_registered.connect_via(app)
    def after_registered_hook(sender):
        sender.logger.info("USER REGISTERED")

    @user_sent_invitation.connect_via(app)
    def after_invitation_hook(sender):
        sender.logger.info("USER SENT INVITATION")

    ### NON-SECURE AREAS (NO LOGIN REQUIRED) ###

    # Map our static assets to be served
    app.register_blueprint(Blueprint('css', __name__, static_url_path=config['rootWebPath'] + '/css', static_folder=str(config['codeRootPathObj'] / 'static' / 'www' / 'css')))
    app.register_blueprint(Blueprint('fonts', __name__, static_url_path=config['rootWebPath'] + '/fonts', static_folder=str(config['codeRootPathObj'] / 'static' / 'www' / 'fonts')))
    app.register_blueprint(Blueprint('img', __name__, static_url_path=config['rootWebPath'] + '/img', static_folder=str(config['codeRootPathObj'] / 'static' / 'www' / 'img')))
    app.register_blueprint(Blueprint('js', __name__, static_url_path=config['rootWebPath'] + '/js', static_folder=str(config['codeRootPathObj'] / 'static' / 'www' / 'js')))

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(str(config['codeRootPathObj'] / 'static' / 'www' / 'img' / 'favicons'), 'favicon.ico')

    ### SECURE AREAS (LOGIN REQUIRED) ###
    ### All methods below should have ###
    ### the @login_required decorator ###

    @app.route(config['rootWebPath']+'/bokeh.html')
    @login_required
    def bokeh():
        return send_from_directory('../www', 'bokeh.html')

    @app.route(config['rootWebPath'] + '/close_all_files', methods=['GET'])
    @login_required
    def close_all_files():

        ### To be implemented here...
        pass

    @app.route(config['rootWebPath'] + '/close_all_project_files', methods=['GET'])
    @login_required
    def close_all_project_files():

        # Parse parameters
        project_id = request.args.get('project_id', type=int)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            return app.response_class(
                response=simplejson.dumps({'success': False}),
                status=200,
                mimetype='application/json'
            )

        ### To be implemented here...

        ### This is the success response -- if there is an error you want to catch, just
        ### the same response below but with success=False!
        return app.response_class(
            response=simplejson.dumps({'success': True}),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath'] + '/close_project_file', methods=['GET'])
    @login_required
    def close_project_file():

        # Parse parameters
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            return app.response_class(
                response=simplejson.dumps({'success': False}),
                status=200,
                mimetype='application/json'
            )

        # Get the file
        file = project.getFile(file_id)
        if file is None:
            logging.error(f"File ID {file_id} not found.")
            return app.response_class(
                response=simplejson.dumps({'success': False}),
                status=200,
                mimetype='application/json'
            )

        ### To be implemented here...

        ### This is the success response -- if there is an error you want to catch, just
        ### the same response below but with success=False!
        return app.response_class(
            response=simplejson.dumps({'success': True}),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath']+'/create_annotation', methods=['GET'])
    @login_required
    def create_annotation():

        # Parse parameters
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)
        left = getFloatParamOrNone('xl')
        right = getFloatParamOrNone('xr')
        top = getFloatParamOrNone('yt')
        bottom = getFloatParamOrNone('yb')
        seriesID = request.args.get('sid')
        label = request.args.get('label')
        pattern_id = request.args.get('pattern_id', type=int)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            return app.response_class(
                response=simplejson.dumps({'success': False}),
                status=200,
                mimetype='application/json'
            )

        # Get the file
        file = project.getFile(file_id)
        if file is None:
            logging.error(f"File ID {file_id} not found.")
            return app.response_class(
                response=simplejson.dumps({'success': False}),
                status=200,
                mimetype='application/json'
            )

        # Write the annotation
        newAnnotationID = file.createAnnotation(current_user.id, left, right, top, bottom, seriesID, label, pattern_id)

        # Output response
        return app.response_class(
            response=simplejson.dumps({'success': True, 'id': newAnnotationID}),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath']+'/delete_annotation')
    @login_required
    def delete_annotation():

        # Parse parameters
        id = request.args.get('id', type=int)
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            return app.response_class(
                response=simplejson.dumps({'success': False}),
                status=200,
                mimetype='application/json'
            )

        # Get the file
        file = project.getFile(file_id)
        if file is None:
            logging.error(f"File ID {file_id} not found.")
            return app.response_class(
                response=simplejson.dumps({'success': False}),
                status=200,
                mimetype='application/json'
            )

        # Write the annotation
        deletionSuccess = file.deleteAnnotation(current_user.id, id)

        # Output response
        return app.response_class(
            response=simplejson.dumps({'success': deletionSuccess}),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath']+'/detect_patterns', methods=['GET'])
    @login_required
    def detect_patterns():

        # TODO(gus): Add checks here

        # Parse the series name and alert parameters
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)
        type = request.args.get('type')
        series = request.args.get('series')
        thresholdlow = request.args.get('thresholdlow', type=float) if request.args.get('thresholdlow') != '' else None
        thresholdhigh = request.args.get('thresholdhigh', type=float) if request.args.get('thresholdhigh') != '' else None
        duration = request.args.get('duration', type=float)
        persistence = request.args.get('persistence', type=float)/100
        maxgap = request.args.get('maxgap', type=float)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            abort(404, description="Project not found.")
            return

        # Get the file
        file = project.getFile(file_id)
        if file is None:
            logging.error(f"File ID {file_id} not found.")
            return app.response_class(
                response=simplejson.dumps([]),
                status=200,
                mimetype='application/json'
            )

        # Run pattern detection
        alerts = file.detectPatterns(
            type=type,
            series=series,
            thresholdlow=thresholdlow,
            thresholdhigh=thresholdhigh,
            duration=duration,
            persistence=persistence,
            maxgap=maxgap
        )

        # Output response
        return app.response_class(
            response=simplejson.dumps(alerts, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath']+'/get_project_annotations')
    @login_required
    def get_project_annotations():

        # Parse parameters
        project_id = request.args.get('project_id', type=int)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            abort(404, description="Project not found.")
            return

        # Assemble project annotations
        projectAnnotations = project.getAnnotationsOutput(current_user.id)

        # Output response
        return app.response_class(
            response=simplejson.dumps(projectAnnotations, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath']+'/')
    @app.route(config['rootWebPath']+'/index.html')
    @login_required
    def index():
        return render_template('index.html', projects=getProjectsPayload(current_user.id), assignments=getAssignmentsPayload(current_user.id))

    @app.route(config['rootWebPath']+'/initial_file_payload')
    @login_required
    def initial_file_payload():

        # Parse parameters
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            abort(404, description="Project not found.")
            return

        # Get the file
        file = project.getFile(file_id)
        if file is None:
            logging.error(f"File ID {file_id} not found.")
            abort(404, description="File not found.")
            return

        # Assemble the initial file payload (full zoomed-out & downsampled, if
        # necessary, datasets for all data series.
        initialFilePayload = file.getInitialPayload(current_user.id)
        
        # Output response
        return app.response_class(
            response=simplejson.dumps(initialFilePayload, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath']+'/project')
    @login_required
    def project():

        # Parse parameters
        id = request.args.get('id', type=int)

        p = getProject(id)
        if p is None:
            logging.error(f"Project ID {id} not found.")
            abort(404, description="Project not found.")
            return

        # Project payload data for the HTML template
        projectPayload = p.getInitialPayload(current_user.id)

        # Assemble the data into a payload. We JSON-encode this twice. The first
        # one converts the dict into JSON. The second one essentially makes the
        # JSON string safe to drop straight into JavaScript code, as we are doing.
        projectPayloadJSON = simplejson.dumps(simplejson.dumps(projectPayload))

        return render_template('project.html', project_name=projectPayload['project_name'], payload=projectPayloadJSON)

    @app.route(config['rootWebPath']+'/series_ranged_data', methods=['GET'])
    @login_required
    def series_ranged_data():

        # Parse parameters
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)
        series = request.args.getlist('s[]')
        start = request.args.get('start', type=float)
        stop = request.args.get('stop', type=float)

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            abort(404, description="Project not found.")
            return

        # Get the file
        file = project.getFile(file_id)
        if file is None:
            logging.error(f"File ID {file_id} not found.")
            abort(404, description="File not found.")
            return

        # Assemble the series ranged data
        seriesRangedData = file.getSeriesRangedOutput(series, start, stop)

        # Output response
        return app.response_class(
            response=simplejson.dumps(seriesRangedData, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath']+'/update_annotation', methods=['GET'])
    @login_required
    def update_annotation():

        # Parse parameters
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)
        id = request.args.get('id')
        left = getFloatParamOrNone('xl')
        right = getFloatParamOrNone('xr')
        top = getFloatParamOrNone('yt')
        bottom = getFloatParamOrNone('yb')
        seriesID = request.args.get('sid')
        label = request.args.get('label')

        # Get the project
        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            return app.response_class(
                response=simplejson.dumps({ 'success': False }),
                status=200,
                mimetype='application/json'
            )

        # Get the file
        file = project.getFile(file_id)
        if file is None:
            logging.error(f"File ID {file_id} not found.")
            return app.response_class(
                response=simplejson.dumps({ 'success': False }),
                status=200,
                mimetype='application/json'
            )

        # Update the annotation
        updateSuccess = file.updateAnnotation(current_user.id, id, left, right, top, bottom, seriesID, label)

        # Output the response
        return app.response_class(
            response=simplejson.dumps({'success': updateSuccess}),
            status=200,
            mimetype='application/json'
        )

    @app.route(config['rootWebPath'] + '/user_manage')
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

def main():

    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog='python -m auviewer.serve', description='Auton Lab Universal Viewer')
    parser.add_argument('datapath', type=str, nargs='?', help='Path to data directory (may be empty if starting new)')
    parser.add_argument('-ds', '--downsample', metavar=('original_file', 'destination_path'), type=str, nargs=2, help='Downsample a single original file to a destination.')
    args = parser.parse_args()

    # Handle a downsample request
    if args.downsample is not None:
        print(f"Downsampling file {Path(args.downsample[0]).resolve()} to destination {Path(args.downsample[1]).resolve()}.")
        downsampleFile(args.downsample[0], args.downsample[1])
        return

    # Handle no data path or file argument
    if args.datapath is None:
        # If no argument provided, prompt user
        assumed_datapath = './auvdata'
        dp = input(f"AUViewer data path [{assumed_datapath}]: ") or assumed_datapath
        logging.info(f"Using data path {dp}")
        set_data_path(dp)

    # Handle single file argument
    elif Path(args.datapath).is_file():

        # If a file was provided, assume it's one-off view timeseries request
        logging.warning("Running viewer against a single file, using a temp directory for data storage (annotations, etc. will be lost).")

        # Establish paths we'll be working wtih
        temp_datapath = Path(tempfile.gettempdir()) / 'auvdata'
        filedir = temp_datapath / 'projects' / 'temp' / 'originals'
        gtdir = temp_datapath / 'global_templates'
        prjtmplt = gtdir / 'project_template.json'

        target_file = Path(args.datapath).resolve()
        symlink_file = filedir / target_file.name

        logging.info(f"Using temporary data path {temp_datapath}")

        # Delete the previous temp data folder if necessary
        if temp_datapath.is_dir():
            shutil.rmtree(temp_datapath)

        # Create temp data, project, and originals folders recursively
        filedir.mkdir(mode=0o700, parents=True, exist_ok=False)

        # Create global templates folder
        gtdir.mkdir(mode=0o700, exist_ok=False)

        # Create a global project template which shows all series by default
        with prjtmplt.open('x') as f:
            print('{ "series": { "_default": { "show": false } } }', file=f)

        # Establish symlink to the target file
        symlink_file.symlink_to(target_file)

        # Set datapath to our temp datapath
        set_data_path(temp_datapath)

    # Handle data path argument
    else:
        # Set the data path provided
        set_data_path(args.datapath)

    app = createApp()

    # Open auviewer in the browser, just before we spin up the server
    browser_url = f"http://{config['host']}{':' + str(config['port']) if str(config['port']) != '80' else ''}/{config['rootWebPath']}".rstrip('/')
    bannerMsgPrefix = '\033[96m\033[1m\033[4m'
    fmtEndSuffix = '\033[0m'
    if args.datapath is not None and Path(args.datapath).is_file():
        print('\033[93m'+"\nNOTE: AUViewer is running against a single file using a temporary directory for data storage. Any annotations, patterns, etc. will be lost!"+fmtEndSuffix)
        print(f"\n{bannerMsgPrefix}You may access your file at: {browser_url}/project?id=1#file_id=1\n{fmtEndSuffix}")
    else:
        print(f"\n{bannerMsgPrefix}You may access AUViewer at: {browser_url}\n{fmtEndSuffix}")

    app.run(host=config['host'], port=config['port'], debug=config['debug'], use_reloader=False)


# Start development web server
if __name__ == '__main__':
    main()
