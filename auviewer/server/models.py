from flask_sqlalchemy import SQLAlchemy
from ..flask_user import UserMixin
from sqlalchemy.sql import func

db = SQLAlchemy()

class Annotation(db.Model):
    __tablename__ = 'annotations'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    series = db.Column(db.String(255), nullable=False)
    left = db.Column(db.Float, nullable=True)
    right = db.Column(db.Float, nullable=True)
    top = db.Column(db.Float, nullable=True)
    bottom = db.Column(db.Float, nullable=True)
    annotation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class AnomalyDetectionRun(db.Model):
    __tablename__ = 'anomaly_detection_runs'
    id = db.Column(db.Integer(), primary_key=True)
    project = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    series = db.Column(db.String(255), nullable=False)
    parameters = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class AnomalyDetectionRunAnomaly(db.Model):
    __tablename__ = 'anomaly_detection_run_anomalies'
    id = db.Column(db.Integer(), primary_key=True)
    anomaly_run_id = db.Column(db.Integer, db.ForeignKey('anomaly_detection_runs.id'))
    filepath = db.Column(db.String(255), nullable=False)
    left = db.Column(db.Float, nullable=True)
    right = db.Column(db.Float, nullable=True)
    top = db.Column(db.Float, nullable=True)
    bottom = db.Column(db.Float, nullable=True)


class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer(), primary_key=True)
    project = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)


class AssignmentItem(db.Model):
    __tablename__ = 'assignment_items'
    id = db.Column(db.Integer(), primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'))
    anomaly_id = db.Column(db.Integer, db.ForeignKey('anomaly_detection_run_anomalies.id'))
    series = db.Column(db.String(255), nullable=False)
    left = db.Column(db.Float, nullable=True)
    right = db.Column(db.Float, nullable=True)
    top = db.Column(db.Float, nullable=True)
    bottom = db.Column(db.Float, nullable=True)


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer(), primary_key=True)
    project_id = db.Column(db.Integer(), db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    #project = db.relationship('Project', backref=db.backref('files', lazy=True))
    path = db.Column(db.String(255), nullable=False)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False, server_default=u'', unique=True)  # for @roles_accepted()


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


# Define the UserRoles association model
class UsersRoles(db.Model):
    __tablename__ = 'users_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


def init_flask_app(app):

    db.init_app(app)

    # Create all database tables
    # TODO(gus): Once we remove flask-user and detach this from flask, move this.
    # with app.app_context():
    #     db.create_all()
    app.app_context().push()
    db.create_all()