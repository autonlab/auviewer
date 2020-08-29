"""Class and related functionality for pattern sets."""

from . import models
from pathlib import Path
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
        self.updateCount()

    # Add patterns to the pattern set.
    def addPatterns(self, df):

        # Subset only the columns we need from the user
        df = df[['file_id', 'series', 'left', 'right', 'top', 'bottom']]

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

    def delete(self):
        models.db.session.delete(self.dbmodel)
        models.db.session.commit()
        del self.projparent.patternsets[self.id]

    def deletePatterns(self):
        models.Pattern.query.filter_by(pattern_set_id=self.id).delete()
        models.db.session.commit()

    def getPatterns(self):
        patterns = [[pattern.file.id, Path(pattern.file.path).name, pattern.series, pattern.left, pattern.right, pattern.top, pattern.bottom] for pattern in self.dbmodel.patterns]
        return pd.DataFrame(patterns, columns=['file_id', 'filename', 'series', 'left', 'right', 'top', 'bottom'])

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

def getAssignments(user_id):
    return [{
        'id': patternset.id,
        'name': patternset.name,
        'description': patternset.description,
        'project_id': patternset.project.id,
        'project_name': patternset.project.name,
        # TODO(gus)
        'completed': 0,
        'remaining': 0,
        'total': 0,
    } for patternset in models.PatternSet.query.filter(models.PatternSet.users.any(id=user_id)).all()]