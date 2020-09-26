"""Class and related functionality for pattern sets."""

from . import models
from pathlib import Path
from sqlalchemy.orm import joinedload
import pandas as pd

class PatternSet:

    def __init__(self, projparent, dbmodel):

        # Holds reference to the project parent
        self.projparent = projparent

        # Set id & name
        self.id = dbmodel.id
        self.name = dbmodel.name

        # Holds the db model
        self.dbmodel = dbmodel

        # Establish a count of patterns belonging to the set
        self.count = 0
        self.updateCount()

    # Add patterns to the pattern set.
    def addPatterns(self, df):

        # Subset only the columns we need from the user
        df = df[['file_id', 'series', 'left', 'right', 'top', 'bottom', 'label']]

        # Add the id of this pattern set
        df.insert(0, "pattern_set_id", [self.id]*df.shape[0])

        # Do the db insert
        df.to_sql('patterns', models.db.engine, index=False, if_exists='append')

        # Update count
        self.updateCount()

    def assignToUsers(self, user_ids):
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
        self.dbmodel.users.extend(
            models.User.query.filter(models.User.id.in_(user_ids)).all()
        )
        models.db.session.commit()

    def delete(self, deletePatterns=False):
        """
        Deletes the pattern set from the database and the parent project
        instance. If the pattern set has patterns, the deletion will fail,
        unless the deletePatterns flag is True, in which case it will first
        delete the child patterns.
        """
        if deletePatterns:
            self.deletePatterns()
        models.db.session.rollback()
        try:
            models.db.session.delete(self.dbmodel)
        except:
            models.db.session.rollback()
            raise
        models.db.session.commit()
        del self.projparent.patternsets[self.id]

    def deletePatterns(self) -> int:
        """
        Delete the patterns belonging to this pattern set.
        :returns: number of deleted patterns
        """
        models.db.session.rollback()
        try:
            n = models.Pattern.query.filter_by(pattern_set_id=self.id).delete()
        except:
            models.db.session.rollback()
            raise
        models.db.session.commit()
        self.updateCount()
        return n

    def deleteUnannotatedPatterns(self) -> int:
        """
        Delete all patterns which have not yet been annotated from the set.
        :returns: number of deleted patterns
        """
        models.db.session.rollback()
        try:
            n = models.Pattern.query.filter(models.Pattern.pattern_set_id == self.id, models.Pattern.id.notin_(
                models.db.session.query(models.Annotation.pattern_id).filter(models.Annotation.pattern_id.isnot(None)).subquery()
            )).delete(synchronize_session=False)
        except:
            models.db.session.rollback()
            raise
        models.db.session.commit()
        self.updateCount()
        return n

    def getAnnotationCount(self) -> int:
        """Returns a count of annotations which annotate any pattern in this set."""
        return models.Annotation.query.filter_by(pattern_set_id=self.id).count()

    def getAnnotations(self) -> pd.DataFrame:
        """Returns a DataFrame of the patterns in this set."""
        return pd.DataFrame(
            [[
                a.file.id,
                Path(a.file.path).name,
                a.user.id, a.user.email,
                a.user.first_name,
                a.user.last_name,
                a.pattern_id,
                a.series,
                a.left,
                a.right,
                a.top,
                a.bottom,
                a.label,
                a.created_at,
                f"{self.projparent.id}{a.file.id}{a.series}{a.left}{a.right}{a.top}{a.bottom}",
            ] for a in models.Annotation.query.options(joinedload('user')).filter_by(pattern_set_id=self.id).all()],
            columns=['file_id', 'filename', 'user_id', 'user_email', 'user_firstname', 'user_lastname', 'pattern_id', 'series', 'left', 'right', 'top', 'bottom', 'label', 'created', 'pattern_identifier']
        )

    def getPatternCount(self) -> int:
        """Returns a count of the patterns in this set."""
        return self.count

    def getPatterns(self) -> pd.DataFrame:
        """Returns a DataFrame of the patterns in this set."""
        pdf = pd.DataFrame(
            [[
                pattern.file.id,
                Path(pattern.file.path).name,
                pattern.series,
                pattern.left,
                pattern.right,
                pattern.top,
                pattern.bottom,
                pattern.label,
                f"{self.projparent.id}{pattern.file.id}{pattern.series}{pattern.left}{pattern.right}{pattern.top}{pattern.bottom}",
            ] for pattern in self.dbmodel.patterns],
            columns=['file_id', 'filename', 'series', 'left', 'right', 'top', 'bottom', 'label', 'pattern_identifier']
        )
        return pdf

    # Set the pattern set's description
    def setDescription(self, description):
        self.dbmodel.description = description
        models.db.session.commit()

    # Set the pattern set's name
    def setName(self, name):
        self.dbmodel.name = name
        models.db.session.commit()
        self.name = name

    # Update the count of patterns belonging to this set
    def updateCount(self):
        self.count = models.Pattern.query.filter_by(pattern_set_id=self.id).count()

def getAssignmentsPayload(user_id):
    return [{
        'id': ps.id,
        'name': ps.name,
        'description': ps.description,
        'project_id': ps.project.id,
        'project_name': ps.project.name,
        'completed': models.Annotation.query.filter_by(user_id=user_id, pattern_set_id=ps.id).count(),
        'remaining': len(ps.patterns) - models.Annotation.query.filter_by(user_id=user_id, pattern_set_id=ps.id).count(),
        'total': len(ps.patterns),
    } for ps in models.PatternSet.query.filter(models.PatternSet.users.any(id=user_id)).all()]