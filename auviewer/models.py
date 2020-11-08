"""Database models and connectivity."""
from . import __VERSION__
from flask_sqlalchemy import SQLAlchemy
from .flask_user import UserMixin
from pkg_resources import packaging
from sqlalchemy.sql import func

db = SQLAlchemy()

class Annotation(db.Model):
    __tablename__ = 'annotations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='RESTRICT'), nullable=False)
    pattern_id = db.Column(db.Integer, db.ForeignKey('patterns.id', ondelete='RESTRICT'), nullable=True)
    pattern_set_id = db.Column(db.Integer, db.ForeignKey('pattern_sets.id', ondelete='RESTRICT'), nullable=True)
    series = db.Column(db.String(255), nullable=False)
    left = db.Column(db.Float, nullable=True)
    right = db.Column(db.Float, nullable=True)
    top = db.Column(db.Float, nullable=True)
    bottom = db.Column(db.Float, nullable=True)
    label = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    file = db.relationship('File', lazy='joined', backref=db.backref('annotations', lazy=True))
    user = db.relationship('User', lazy=True)

    def __repr__(self):
        return f"ID: {self.id}, UID: {self.user_id}, PID: {self.project_id}, FID: {self.file_id}, PID: {self.pattern_id}, Series: {self.series}, Boundaries: {self.left} {self.right} {self.top} {self.bottom}, Label: {self.label}"

class Pattern(db.Model):
    __tablename__ = 'patterns'
    id = db.Column(db.Integer, primary_key=True)
    pattern_set_id = db.Column(db.Integer, db.ForeignKey('pattern_sets.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable=False)
    series = db.Column(db.String(255), nullable=False)
    left = db.Column(db.Float, nullable=True)
    right = db.Column(db.Float, nullable=True)
    top = db.Column(db.Float, nullable=True)
    bottom = db.Column(db.Float, nullable=True)
    label = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    annotations = db.relationship('Annotation', lazy=True, backref=db.backref('pattern', lazy=True))
    file = db.relationship('File', lazy='joined', backref=db.backref('patterns', lazy=True))

    def __repr__(self):
        return f"ID: {self.id}, PSID: {self.pattern_set_id}, FID: {self.file_id}, Series: {self.series}, Boundaries: {self.left} {self.right} {self.top} {self.bottom}, Label: {self.label}" + (f"\n    Annotations: {self.annotations}" if len(self.annotations)>0 else "")


# Many-to-many table joining pattern sets to users vis-a-vis assignments
patternSetAssignments = db.Table('pattern_set_assignments',
    db.Column('pattern_set_id', db.Integer, db.ForeignKey('pattern_sets.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)


class PatternSet(db.Model):
    __tablename__ = 'pattern_sets'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    show_by_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    annotations = db.relationship('Annotation', lazy=True)
    patterns = db.relationship('Pattern', lazy=True)
    project = db.relationship('Project', lazy='joined', backref=db.backref('pattern_sets', lazy=True))
    users = db.relationship('User', secondary=patternSetAssignments, lazy=True, backref=db.backref('pattern_sets', lazy=True))


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    #project = db.relationship('Project', backref=db.backref('files', lazy=True))
    path = db.Column(db.String(255), nullable=False)


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
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

    # Other
    assignments_remaining = db.Column(db.Integer, nullable=False, default=0)


class UserInvitation(db.Model):
    __tablename__ = 'user_invite'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    # save the user of the invitee
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # token used for registration page to identify user registering
    token = db.Column(db.String(100), nullable=False, server_default='')


# The version table holds a single row with a single column and stores
# the auviewer version which the database matches.
class Version(db.Model):
    __tablename__ = 'version'
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(255), nullable=False)


# Define the UserRoles association model
class UsersRoles(db.Model):
    __tablename__ = 'users_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'))


def init_flask_app(app):

    db.init_app(app)

    # Create all database tables
    # TODO(gus): Once we remove flask-user and detach this from flask, move this.
    with app.app_context():

        # Create database & tables, if needed
        db.create_all()

        # Perform db upgrades, if needed
        upgrade_db()

    # app.app_context().push()
    # db.create_all()

# Perform any db version upgrades necessary
def upgrade_db():

    # Get auviewer package version
    app_version = packaging.version.parse(__VERSION__)

    # Check application version, and upgrade iteratively as needed
    while True:

        # Get db version
        dvm = Version.query.first()

        # If there is no version, assume 0.1.1rc4 (after this, db
        # versioning began) and write this to the database.
        if dvm is None:
            db.session.add(Version(id=0, version='0.1.1rc4'))
            db.session.commit()
            continue

        db_version = packaging.version.parse(dvm.version)

        # ADD DB UPGRADE STEPS LIKE THIS:
        # if db_version < packaging.version.parse('x.x.x'):
        #     do_some_db_upgrade()
        #     Version.query.first().version = 'x.x.x'
        #     db.session.commit()
        #     continue

        if db_version != app_version:
            Version.query.first().version = __VERSION__
            db.session.commit()

        # We've completed all db upgrades, so break the loop
        break