"""Class and related functionality for pattern sets."""

from pathlib import Path
from sqlalchemy.orm import joinedload
import pandas as pd
from typing import Union, List

from . import models
from .shared import annotationDataFrame, patternDataFrame

class PatternSet:

    def __init__(self, projparent, dbmodel):

        # Holds reference to the project parent
        self.projparent = projparent

        # Set id & name
        self.id = dbmodel.id
        self.name = dbmodel.name
        self.showByDefault = dbmodel.show_by_default

        # Holds the db model
        self.dbmodel = dbmodel

        # Establish a count of patterns belonging to the set
        self.count = 0
        self.updateCount()

    # Add patterns to the pattern set.
    def addPatterns(self, df):

        # Subset only the columns we need from the user
        df = df[['file_id', 'series', 'left', 'right', 'top', 'bottom', 'label']]

        # Add the project ID
        df['project_id'] = self.projparent.id

        # Add the id of this pattern set
        df.insert(0, "pattern_set_id", [self.id]*df.shape[0])

        # Do the db insert
        df.to_sql('patterns', models.db.engine, index=False, if_exists='append')

        # Update count
        self.updateCount()

    def assignToUsers(self, user_ids: Union[int, List[int]]) -> None:
        """
        Assign the pattern set to user(s).
        :param user_ids: May be single user ID or list of user IDs.
        :return: None
        """
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
        :return: number of deleted patterns
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
        :return: number of deleted patterns
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
        """Returns a DataFrame of the annotations in this set."""
        return annotationDataFrame(models.Annotation.query.options(joinedload('user')).filter_by(pattern_set_id=self.id).all())

    def getPatternCount(self) -> int:
        """Returns a count of the patterns in this set."""
        return self.count

    def getPatterns(self) -> pd.DataFrame:
        """Returns a DataFrame of the patterns in this set."""
        return patternDataFrame(self.dbmodel.patterns)

    # Set the pattern set's description
    def setDescription(self, description: str):
        """Set the pattern set's description."""
        self.dbmodel.description = description
        models.db.session.commit()

    # Set the pattern set's name
    def setName(self, name: str):
        """Set the pattern set's name."""
        self.dbmodel.name = name
        models.db.session.commit()
        self.name = name

    def setShowByDefault(self, show: bool):
        """Set whether a pattern set should show by default."""
        self.dbmodel.show_by_default = show
        models.db.session.commit()
        self.showByDefault = show

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