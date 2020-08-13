from flask import Flask, Blueprint, send_from_directory, request, render_template, render_template_string
from flask_mail import Mail
from flask_socketio import SocketIO, join_room, leave_room, rooms
from htmlmin.main import minify
from pprint import pprint
import os
import argparse

# Simplejson package is required in order to "ignore" NaN values and implicitly
# convert them into null values. RFC JSON spec left out NaN values, even though
# ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the
# Chrome JS engine will throw an error when trying to parse them. Simplejson
# package, with ignore_nan=True, will implicitly convert NaN values into null
# values. Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson

from . import models
from .config import set_data_path, config, FlaskConfigClass
from .file import File
from .project import load_projects

from ..flask_user import confirm_email_required, current_user, login_required, UserManager, SQLAlchemyAdapter
from ..flask_user.signals import user_sent_invitation, user_registered

def create_app():

    # Instantiate the Flask web application class
    app = Flask(__name__, template_folder=config['auvCodeRoot']+'/static/www/templates')

    # Instantiate SocketIO
    socketio = SocketIO(app)

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
    #models.db.init_app(app)
    #models.db.create_all(app)

    # Initialize Flask-Mail
    mail = Mail(app)

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(models.db, models.User, UserInvitationClass=models.UserInvitation)  # Select database adapter
    user_manager = UserManager(db_adapter, app)  # Init Flask-User and bind to app

    # You may use this code snippet below to create initial/new admin users
    # (since it is not possible through the interface). Alternatively, you
    # could modify the database.
    #
    # new_admin_email = 'gwelter@andrew.cmu.edu'
    # new_admin_pass = 'akeminute'
    # if not User.query.filter(User.email == new_admin_email).first():
    #     u = User(email=new_admin_email, active=True, password=user_manager.hash_password(new_admin_pass))
    #     u.roles.append(Role(name='admin'))
    #     db.session.add(u)
    #     db.session.commit()

    # Load projects
    load_projects()

    # Instantiate a file for realtime, in-memory usage (probably temporary)
    # TODO(gus): Refactor realtime
    #rtf = File(projparent=None)

    @user_registered.connect_via(app)
    def after_registered_hook(sender, user, user_invite):
        sender.logger.info("USER REGISTERED")

    @user_sent_invitation.connect_via(app)
    def after_invitation_hook(sender, **extra):
        sender.logger.info("USER SENT INVITATION")

    # Map our static assets to be served
    app.register_blueprint(Blueprint('css', __name__, static_url_path=config['rootWebPath']+'/css', static_folder=os.path.join(config['auvCodeRoot'], 'static/www/css')))
    app.register_blueprint(Blueprint('fonts', __name__, static_url_path=config['rootWebPath']+'/fonts', static_folder=os.path.join(config['auvCodeRoot'], 'static/www/fonts')))
    app.register_blueprint(Blueprint('js', __name__, static_url_path=config['rootWebPath']+'/js', static_folder=os.path.join(config['auvCodeRoot'], 'static/www/js')))

    ### NON-SECURE AREAS (NO LOGIN REQUIRED) ###

    @app.route(config['rootWebPath']+'/anyone')
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

    @app.route(config['rootWebPath']+'/user_manage')
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
    ### All methods below should have ###
    ### the @login_required decorator ###

    @app.route(config['rootWebPath']+'/bokeh.html')
    @login_required
    def bokeh():
        return send_from_directory('../www', 'bokeh.html')

    @app.route(config['rootWebPath']+'/create_annotation', methods=['GET'])
    @login_required
    def create_annotation():

        # Parse parameters
        projname = request.args.get('project')
        filename = request.args.get('file')
        left = getFloatParamOrNone('xl')
        right = getFloatParamOrNone('xr')
        top = getFloatParamOrNone('yt')
        bottom = getFloatParamOrNone('yb')
        seriesID = request.args.get('sid')
        label = request.args.get('label')

        # Try to get the project
        try:

            # Get the project
            project = projects[projname]

        except:

            print("Project could not be retrieved:", projname)
            return simplejson.dumps({
                'success': False
            })

        # Get the file
        file = project.getFile(filename)

        # If we did not find the file, return empty output
        if not isinstance(file, File):
            print("File could not be retrieved:", filename)
            return simplejson.dumps({
                'success': False
            })

        # Write the annotation
        return simplejson.dumps({
            'success': True,
            'id': file.annotationSet.createAnnotation(left, right, top, bottom, seriesID, label)
        })

    @app.route(config['rootWebPath']+'/delete_annotation')
    @login_required
    def delete_annotation():

        # Parse parameters
        id = request.args.get('id')
        projname = request.args.get('project')
        filename = request.args.get('file')

        # Try to get the project
        try:

            # Get the project
            project = projects[projname]

        except:

            print("Project could not be retrieved:", projname)
            return simplejson.dumps({
                'success': False
            })

        # Get the file
        file = project.getFile(filename)

        # If we did not find the file, return empty output
        if not isinstance(file, File):
            print("File could not be retrieved:", filename)
            return simplejson.dumps({
                'success': False
            })

        # Delete the annotation
        return simplejson.dumps({
            'success': file.annotationSet.deleteAnnotation(id)
        })

    @app.route(config['rootWebPath']+'/detect_anomalies', methods=['GET'])
    @login_required
    def detect_anomalies():

        # TODO(gus): Add checks here

        # Parse the series name and alert parameters
        projname = request.args.get('project')
        filename = request.args.get('file')
        type = request.args.get('type')
        series = request.args.get('series')
        thresholdlow = request.args.get('thresholdlow', type=float) if request.args.get('thresholdlow') != '' else None
        thresholdhigh = request.args.get('thresholdhigh', type=float) if request.args.get('thresholdhigh') != '' else None
        duration = request.args.get('duration', type=float)
        persistence = request.args.get('persistence', type=float)/100
        maxgap = request.args.get('maxgap', type=float)

        # Try to get the project
        try:

            # Get the project
            project = projects[projname]

        except:

            print("Project could not be retrieved:", projname)
            return simplejson.dumps([])

        # Get the file
        file = project.getFile(filename)

        # If we did not find the file, return empty output
        if not isinstance(file, File):
            print("File could not be retrieved:", filename)
            return ''

        alerts = file.detectAnomalies(
            type=type,
            series=series,
            thresholdlow=thresholdlow,
            thresholdhigh=thresholdhigh,
            duration=duration,
            persistence=persistence,
            maxgap=maxgap
        )

        return simplejson.dumps(alerts, ignore_nan=True)

    @app.route(config['rootWebPath']+'/get_project_annotations')
    @login_required
    def get_project_annotations():

        # Parse parameters
        projname = request.args.get('project')

        # Get the project
        try:
            project = projects[projname]
        except:
            print("Project could not be retrieved:", projname)
            return simplejson.dumps({})

        output = project.getAnnotations()
        json_output = simplejson.dumps(output, ignore_nan=True)

        return json_output

    @app.route(config['rootWebPath']+'/initial_payload')
    @login_required
    def initial_payload():

        #TODO(gus): This is hacked together temporarily. Move to permanent home.

        builtin_default_project_template = simplejson.dumps({})
        builtin_default_interface_templates = simplejson.dumps({})
        global_default_project_template = simplejson.dumps({})
        global_default_interface_templates = simplejson.dumps({})

        try:
            with open(os.path.join(config['auvCodeRoot'], 'static/builtin_templates/project_template.json'), 'r') as f:
                builtin_default_project_template = f.read()
        except:
            pass
        try:
            with open(os.path.join(config['auvCodeRoot'], 'static/builtin_templates/interface_templates.json'), 'r') as f:
                builtin_default_interface_templates = f.read()
        except:
            pass
        try:
            with config['globalDefaultProjectTemplateFilePathObj'].open() as f:
                global_default_project_template = f.read()
        except:
            pass
        try:
            with config['globalDefaultInterfaceTemplatesFilePathObj'].open() as f:
                global_default_interface_templates = f.read()
        except:
            pass

        response = {
            'projects': list(projects.keys()),
            'builtin_default_project_template': builtin_default_project_template,
            'builtin_default_interface_templates': builtin_default_interface_templates,
            'global_default_project_template': global_default_project_template,
            'global_default_interface_templates': global_default_interface_templates
        }

        return simplejson.dumps(response)

    @app.route(config['rootWebPath']+'/')
    @app.route(config['rootWebPath']+'/index.html')
    @login_required
    def index():
        #return send_from_directory('../www', 'index.html')
        return render_template('index.html')

    @app.route(config['rootWebPath']+'/initial_file_payload')
    @login_required
    def initial_file_payload():

        if request.method == 'GET' and len(request.args.get('file', default='')) > 0:

            # Parse parameters
            projname = request.args.get('project')
            filename = request.args.get('file')

            # If the user is in realtime mode, select the realtime file.
            if projname == '__realtime__' and filename == '__realtime__':

                file = rtf

            else:

                # Get the project
                try:
                    project = projects[projname]
                except:
                    print("Project could not be retrieved:", projname)
                    return simplejson.dumps({})

                # Get the file
                file = project.getFile(filename)

            # If we did not find the file, return empty output
            if not isinstance(file, File):
                return ''

            # Return the full (zoomed-out but downsampled if appropriate) datasets for
            # all data series.
            output = file.getInitialPayloadOutput()
            json_output = simplejson.dumps(output, ignore_nan=True)

            return json_output

        else:
            return "Invalid request."

    @app.route(config['rootWebPath']+'/initial_project_payload')
    @login_required
    def initial_project_payload():

        # Parse parameters
        projname = request.args.get('project')

        # Try to get the project
        try:

            # Get the project
            project = projects[projname]

        except:

            print("Project could not be retrieved:", projname)
            return simplejson.dumps([])

        output = project.getInitialPayloadOutput()
        json_output = simplejson.dumps(output)

        return json_output

    @app.route(config['rootWebPath']+'/series_ranged_data', methods=['GET'])
    @login_required
    def series_ranged_data():

        if request.method == 'GET' and len(request.args.get('file', default='')) > 0 and len(
                request.args.get('start', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(
                request.args.get('stop', default='')) > 0:

            # Parse the series name and start & stop times
            projname = request.args.get('project')
            filename = request.args.get('file')
            series = request.args.getlist('s[]')
            start = request.args.get('start', type=float)
            stop = request.args.get('stop', type=float)

            # Try to get the project
            try:

                # Get the project
                project = projects[projname]

            except:

                print("Project could not be retrieved:", projname)
                return simplejson.dumps({})

            # Get the file
            file = project.getFile(filename)

            # If we did not find the file, return empty output
            if not isinstance(file, File):
                return ''

            output = file.getSeriesRangedOutput(series, start, stop)
            json_output = simplejson.dumps(output, ignore_nan=True)

            return json_output

    @app.route(config['rootWebPath']+'/update_annotation', methods=['GET'])
    @login_required
    def update_annotation():

        # Parse parameters
        projname = request.args.get('project')
        filename = request.args.get('file')
        id = request.args.get('id')
        left = getFloatParamOrNone('xl')
        right = getFloatParamOrNone('xr')
        top = getFloatParamOrNone('yt')
        bottom = getFloatParamOrNone('yb')
        seriesID = request.args.get('sid')
        label = request.args.get('label')

        # Try to get the project
        try:

            # Get the project
            project = projects[projname]

        except:

            print("Project could not be retrieved:", projname)
            return simplejson.dumps({
                'success': False
            })

        # Get the file
        file = project.getFile(filename)

        # If we did not find the file, return empty output
        if not isinstance(file, File):
            print("File could not be retrieved:", filename)
            return simplejson.dumps({
                'success': False
            })

        # Write the annotation
        return simplejson.dumps({
            'success': file.annotationSet.updateAnnotation(id, left, right, top, bottom, seriesID, label)
        })

    @socketio.on('add_data')
    def handle_add_data(json):

        if config['verbose']:
            print('received socketio: add_data')
            print('msg data:', json)

        try:

            updates = rtf.addSeriesData(json)

            # Broadcast the new data to subscribers
            socketio.emit('new_data', updates, room='__realtime____^^____realtime__')

        except Exception as e:

            # TODO(gus): Report an error to user in a websocket response
            raise e

    @socketio.on('push_template')
    def handle_push_template(json):

        if config['verbose']:
            print('received socketio: push_template')
            print('msg data:', json)

        # Verify we have the template in the dict
        if 'template' not in json:
            print('Error: handle_push_template did not receive template (data.template not found):', json)

        # JSONify the template if not already
        if not isinstance(json['template'], str):
            json['template'] = simplejson.dumps(json['template'])

        socketio.emit('push_template', json, broadcast=True)

    @socketio.on('subscribe')
    def handle_subscribe(json):

        if config['verbose']:
            print('received socketio: subscribe')
            print('msg data:', json)

        try:

            # Subscribe the user to realtime updates
            subscribe_to_realtime_updates(json['project'], json['filename'])

        except Exception as e:

            # TODO(gus): Report an error to user in a websocket response
            raise e

    @socketio.on('unsubscribe')
    def handle_unsubscribe():

        if config['verbose']:
            print('received socketio: unsubscribe')

        try:

            # Subscribe the user to realtime updates
            unsubscribe_from_realtime_updates()

        except Exception as e:

            # TODO(gus): Report an error to user in a websocket response
            raise e

    ### HELPERS ###

    # Returns the named request parameter as a float or None if the parameter is
    # empty or not present. The default return of None may be overridden.
    def getFloatParamOrNone(name, default=None):
        param = request.args.get(name)
        if param is not None and len(param) > 0:
            return request.args.get(name, type=float)
        else:
            return default

    return (app, socketio)

def subscribe_to_realtime_updates(project, file):

    # NOTE: It is not really necessary to track which project & file the user is
    # subscribed to since, currently, it is only possible to subscribe to the
    # realtime file (__realtime__, __realtime__). However, it was trivial to add
    # this and it enables future expansion to have more than one realtime file.

    # Unsubscribe the user from any rooms exception own sid
    unsubscribe_from_realtime_updates()

    # Name of new room to subscribe to
    room = project + '__^^__' + file

    # Subscribe the user to the new room (project)
    join_room(room)

    print('User', request.sid, 'has been subscribed to', room)

def unsubscribe_from_realtime_updates():

    # Get the user's sid
    sid = request.sid

    # Unsubscribe the user from any rooms exception own sid
    for r in rooms():
        if r != sid:
            leave_room(r)
            print('User', request.sid, 'has been unsubscribed from', r)

def main():

    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog='python -m auviewer.server.serve', description='Auton Lab Universal Viewer')
    parser.add_argument('datapath', type=str, help='Path to data directory (may be empty if starting new)')
    args = parser.parse_args()

    # Set provided data path
    set_data_path(args.datapath)\

    (app, socketio) = create_app()
    socketio.run(app,
        host=config['host'],
        port=config['port'],
        debug=config['debug'],
        use_reloader=config['reloader'])

# Start development web server
if __name__ == '__main__':
    main()
