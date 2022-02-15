from flask import Flask, Blueprint, send_from_directory, request, render_template, render_template_string, abort, Markup
from flask_mail import Mail
from htmlmin.main import minify
from pathlib import Path
from pprint import pprint
import argparse
import logging
import shutil
import tempfile
import json

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

from .flask_user import current_user, login_required, UserManager, SQLAlchemyAdapter
from .flask_user.signals import user_sent_invitation, user_registered






##### IMPORTS FOR FEATURIZERS
from sklearn.linear_model import LinearRegression

from datetime import datetime
import pandas as pd
import numpy as np
import pytz

###
### Featurizer functionality - disabled for release
###
# from .modules.featurization.example import ExampleFeaturizer
# from .modules.featurization.mean import MeanFeaturizer
# from .modules.featurization.std import StandardDeviationFeaturizer
# from functools import partial
#
# # Dict of featurizers indexed by ID
# featurizers = { f.id: f for f in [
#     ExampleFeaturizer(),
#     MeanFeaturizer(),
#     StandardDeviationFeaturizer(),
#     CoeffOfVariationFeaturizer(),
#     MADFeaturizer(),
#     NFeaturizer(),
#     MinFeaturizer(),
#     MaxFeaturizer(),
#     MedianFeaturizer(),
#     RangeFeaturizer(),
#     RangeRatioFeaturizer(),
#     DataDenFeaturizer(),
#     MaxGapFeaturizer(),
#     LRSlopeFeaturizer(),
#     RobustSlopeFeaturizer(),
# ]}
featurizers = {}


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
        projects = getProjectsPayload(current_user.id)

        for p in projects:
            proj = getProject(p['id'])
            for f in proj.files:
                try:
                    f.close()

                except Exception as e:
                    return app.response_class(
                            response=simplejson.dumps({'success': False}),
                            status=200,
                            mimetype='application/json'
                        )

        ### To be implemented here...
        return app.response_class(
            response=simplejson.dumps({'success': True}),
            status=200,
            mimetype='application/json'
        )

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
        for f in project.files:
            try:
                f.close()
            except Exception as e:
                print(e)
                return app.response_class(
                        response=simplejson.dumps({'success': False}),
                        status=200,
                        mimetype='application/json'
                    )

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
        try:
            file.close()
        except Exception as e:
            return app.response_class(
                response=simplejson.dumps({'success':False}),
                status=200,
                mimetype='application/json'
            )

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
            logging.error(f"Project ID '{project_id}' not found.")
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

    @app.route(config['rootWebPath'] + '/featurize')
    @login_required
    def featurize():

        # Parse parameters
        featurizer = request.args.get('featurizer')
        project_id = request.args.get('project_id', type=int)
        file_id = request.args.get('file_id', type=int)
        series = request.args.get('series')
        left = request.args.get('left', type=float)
        right = request.args.get('right', type=float)
        params = json.loads(request.args.get('params'));

        print("\n".join([
            f"\nFeaturizer {featurizer} requested, with parameters:",
            f"Project ID: {project_id}",
            f"File ID: {file_id}",
            f"Series: {series}",
            f"Left: {left}",
            f"Right: {right}",
            f"Params: {params}\n",
        ]))

        if featurizer in featurizers:
            featurizerFunction = featurizers[featurizer].getFeaturizeFunction(params)
        else:
            raise Exception(f"Unknown featurizer requested: {featurizer}")

        try:

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
                    response=simplejson.dumps({'success': False}),
                    status=200,
                    mimetype='application/json'
                )

            utc = pytz.UTC

            s = file.getSeries(series)
            if s is None:
                raise Exception('series not found')
            df = s.getDataAsDF().set_index('time')
            window_size = params['window_size']

            # # Option 1 (sometimes this works) – make sure to correlate with option above
            left = datetime.fromtimestamp(left).astimezone(utc)
            right = datetime.fromtimestamp(right).astimezone(utc)

            # Option 2 (and sometimes this works) – make sure to correlate with option above
            # left = np.datetime64(datetime.fromtimestamp(left).astimezone(utc))
            # right = np.datetime64(datetime.fromtimestamp(right).astimezone(utc))

            # # This was from an earlier attempt, probably discard...
            # left = pd.to_datetime(datetime.fromtimestamp(left).astimezone(utc))
            # right = pd.to_datetime(datetime.fromtimestamp(right).astimezone(utc))

            df = df[(df.index >= left) & (df.index <= right)]

            # TODO: Might make label side configurable

            featurization = df.resample(window_size, label='right').agg(featurizerFunction).replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna().reset_index()
            print(featurization)

            # Option 1 (sometimes this works) – make sure to correlate with option above
            featurization['time'] = ((featurization['time'].dt.tz_convert(utc) - pd.Timestamp("1970-01-01").replace(tzinfo=utc)) // pd.Timedelta("1ms")) / 1000

            # Option 2 (and sometimes this works) – make sure to correlate with option above
            # featurization['time'] = ((featurization['time'].dt.tz_localize('UTC') - pd.Timestamp("1970-01-01").replace(tzinfo=utc)) // pd.Timedelta("1ms")) / 1000

            nones = [None] * featurization.shape[0]
            data = [list(i) for i in zip(featurization['time'], nones, nones, featurization['value'])]
            response = {
                'id': f"{window_size}_{featurizer}_{series}",
                'success': True,
                'labels': ['Date/Offset', 'Min', 'Max', 'Sample Entropy for '+series],
                'data': data,
                'output_type': 'real',
                'temporary': True,
            }

            # Output response
            return app.response_class(
                response=simplejson.dumps(response, ignore_nan=True),
                status=200,
                mimetype='application/json',
            )

        except Exception as e:

            logging.error("There was an exception while featurizing.", exc_info=True)

            response = {
                'success': False,
                'error_message': f"There was an error while featurizing: {e}",
            }

            return app.response_class(
                response=simplejson.dumps(response, ignore_nan=True),
                status=200,
                mimetype='application/json',
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

    # @app.route(config['rootWebPath']+'/initial_evaluator_payload')
    # @login_required
    def initial_evaluator_payload():
        project_id = request.args.get('project_id', type=int)

        project = getProject(project_id)
        res = dict()
        res = project.applyLabelModel()
        return app.response_class(
            response=simplejson.dumps(res, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/reprioritize_file')
    # @login_required
    def prioritize_file():
        project_id = request.args.get('project_id', type=int)
        file_idx = request.args.get('file_idx', type=int)

        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            abort(404, description="Project not found.")
            return
        try:
            project.file_ids
        except:
            fileIds = [f.id for f in project.files]
            project.file_ids = fileIds

        fileIds = project.file_ids
        if file_idx < 0 or file_idx > len(fileIds):
            return 
        fileIds = [fileIds[file_idx]] + fileIds[:file_idx] + fileIds[file_idx+1:]
        project.file_ids = fileIds

        filesPayload = project.queryWeakSupervision({
            'randomFiles': False,
            # 'amount': 5
        }, fileIds = fileIds)

        _ = project.populateInitialSupervisorValuesToDict(fileIds, filesPayload)
        filesPayload['thresholds'] = project.getThresholdsPayload()
        filesPayload['existent_segments'], _ = project.getSegments()
        return app.response_class(
            response=simplejson.dumps(filesPayload, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/initial_supervisor_payload')
    # @login_required
    def initial_supervisor_payload():
        project_id = request.args.get('project_id', type=int)

        project = getProject(project_id)
        if project is None:
            logging.error(f"Project ID {project_id} not found.")
            abort(404, description="Project not found.")
            return

        fileIds = [f.id for f in project.files]
        filesPayload = project.queryWeakSupervision({
            'randomFiles': False,
            # 'amount': 5
        }, fileIds = fileIds)
        # {
        #     'randomFiles': bool,
        #     'categorical': List[Category],
        #     'labelingFunction': str,
        #     'amount': int,
        #     # 'sortByConfidence': bool,
        #     # 'patientSearchString': str,
        # }
        # supervisorPayload = project.queryWeakSupervision({
        #     'randomFiles': True,
        #     'categorical': None,
        #     'labelingFunction': None,
        #     'amount': 10
        # })
        _ = project.populateInitialSupervisorValuesToDict(fileIds, filesPayload)
        filesPayload['thresholds'] = project.getThresholdsPayload()
        filesPayload['existent_segments'], _ = project.getSegments()
        return app.response_class(
            response=simplejson.dumps(filesPayload, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/get_labels')
    # @login_required
    def get_labels():
        project_id = request.args.get('project_id', type=int)

        labels = getProject(project_id).getLabels()
        return app.response_class(
            response=simplejson.dumps({'possible_labels': list(labels.keys())}, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/get_labelers')
    # @login_required
    def get_labelers():
        project_id = request.args.get('project_id', type=int)

        labelers = getProject(project_id).getLabelers()
        return app.response_class(
            response=simplejson.dumps({'possible_labelers': labelers}, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/get_segments')
    # @login_required
    def get_segments():
        project_id = request.args.get('project_id', type=int)
        type = request.args.get('segment_type', type=str)

        segments, windowInfo = getProject(project_id).getSegments(type)
        return app.response_class(
            response=simplejson.dumps({'segments': segments, 'window_info': windowInfo}, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/get_labeler_statistics')
    # @login_required
    def get_labeler_stats():
        project_id = request.args.get('project_id', type=int)
        segment_type = request.args.get('segment_type', type=str)

        project = getProject(project_id)
        stats = project.getLFStats(segment_type)

        return app.response_class(
            response=simplejson.dumps(stats, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/update_threshold', methods=['PUT'])
    # @login_required
    def put_threshold():
        project_id = request.args.get('project_id', type=int)
        p = getProject(project_id)
        req = request.get_json()
        success = p.updateThreshold(req)
        print(success)
        return app.response_class(
            response=simplejson.dumps({'success': success}, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/delete_vote_segments', methods=['POST'])
    # @login_required
    def delete_vote_segments():
        project_id = request.args.get('project_id', type=int)
        project = getProject(project_id)

        payload = request.get_json()
        voteSegments = payload['vote_segments']
        numDeleted, success = project.deleteSegments(voteSegments)

        returnPayload = {
            'success': success,
            'number_deleted': numDeleted
        }

        return app.response_class(
            response=simplejson.dumps(returnPayload, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/create_vote_segments', methods=['POST'])
    # @login_required
    def create_vote_segments():
        project_id = request.args.get('project_id', type=int)
        project = getProject(project_id)

        payload = request.get_json()
        voteSegments = payload.get('vote_segments')
        windowInfo = payload.get('window_info')
        createdSegments, success, numAdded = project.createSegments(voteSegments, windowInfo)

        returnPayload = {
            'newly_created_segments': createdSegments,
            'success': success,
            'num_added': numAdded
            }

        return app.response_class(
            response=simplejson.dumps(returnPayload, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/preview_threshold_change', methods=['POST'])
    # @login_required
    def preview_threshold():
        project_id = request.args.get('project_id', type=int)
        project = getProject(project_id)

        req = request.get_json()
        file_ids = req['files']
        thresholds = req['thresholds']
        labeler = req['labeler']
        timeSegment = req['time_segment']

        voteOutputs, endIndicesOutputs = project.previewThresholds(file_ids, thresholds, labeler, timeSegment)
        returnLoad = {'votes': voteOutputs,
            'end_indices': endIndicesOutputs}

        return app.response_class(
            response=simplejson.dumps(returnLoad, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/get_votes', methods=["GET", "POST"])
    # @login_required
    def get_votes():
        project_id = request.args.get('project_id', type=int)
        recalculate = request.args.get('recalculate', type=bool)
        fileIds = request.args.getlist('file_ids[]')
        windowInfo = request.get_json()['window_info']
        '''
            window_info: {
                window_size_ms: 30*60*1000,
                window_roll_ms: 30*60*1000
            }
        '''

        project = getProject(project_id)
        if (len(fileIds) == 0):
            fileIds = [f.id for f in project.files]
        print(fileIds, windowInfo)
        fileIds = [int(fileId) for fileId in fileIds]
        if (len(models.Vote.query.filter_by(project_id=project_id).all()) > 0):
            print('getting votes instead')
            votes, preds = project.getVotes(fileIds, windowInfo)
            d = dict()
            d['lm_predictions'] = preds
        else:
            votes = project.computeVotes(fileIds, windowInfo)
            d = dict()
        d['labeling_function_votes'] = votes
        return app.response_class(
            response=simplejson.dumps(d, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/query_supervisor_series', methods=['POST'])
    # @login_required
    def query_supervisor_series():
        project_id = request.args.get('project_id', type=int)
        request_data = request.get_json()
        query_payload = request_data['query_payload']

        project = getProject(project_id)
        query_response = project.queryWeakSupervision(query_payload)
        _ = project.populateInitialSupervisorValuesToDict([f[0] for f in query_response['files']], query_response)
        return app.response_class(
            response=simplejson.dumps(query_response),
            status=200,
            mimetype='application/json'
        )

    # @app.route(config['rootWebPath']+'/upload_custom_segments', methods=['POST'])
    # @login_required
    def custom_segments_upload():
        project_id = request.args.get('project_id', type=int)
        p = getProject(project_id)
        file = request.files['file_payload']

        segments, count = p.parseAndCreateSegmentsFromFile(file.filename, file)
        return app.response_class(
            response=simplejson.dumps({'segments': segments, 'num_added': count}),
            status=200,
            mimetype='application/json'
        )
        #receives function that takes in patient series' and returns necessary inputs for LF votes

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








        #### TEMP FOR FEATURIZERS

        # Assemble the data into a payload. We JSON-encode this twice. The first
        # one converts the dict into JSON. The second one essentially makes the
        # JSON string safe to drop straight into JavaScript code, as we are doing.
        featurizersJSONPayload = simplejson.dumps(simplejson.dumps({
            f.id: {
                'id': f.id,
                'name': f.name,
                'fields': f.getFields(),
            } for f in featurizers.values()
        }))

        # m = MeanFeaturizer()
        #
        # # Assemble the data into a payload. We JSON-encode this twice. The first
        # # one converts the dict into JSON. The second one essentially makes the
        # # JSON string safe to drop straight into JavaScript code, as we are doing.
        # featurizersJSONPayload = simplejson.dumps(simplejson.dumps(m.getFields()))







        return render_template('project.html', project_name=projectPayload['project_name'], payload=projectPayloadJSON, featurizersJSONPayload=featurizersJSONPayload)

    # @app.route(config['rootWebPath']+'/supervisor')
    # @login_required
    def supervisor():
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

        return render_template('supervisor.html', project_name=projectPayload['project_name'], payload=projectPayloadJSON)

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
    return app


# Start development web server
if __name__ == '__main__':
    app = main()
