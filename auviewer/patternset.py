"""Class and related functionality for pattern sets."""

from sqlalchemy.orm import joinedload
import pandas as pd
from typing import Union, List

from . import models
from .shared import annotationDataFrame, patternDataFrame

class PatternSet:
    """Represents a pattern set."""

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

        # Refresh model & count
        self.refresh()

    def addPatterns(self, df, validate=True):
        """
        Add patterns to the pattern set. By default, the rows will be validated (e.g. for matching file ID & filename).
        This may be skipped in the case of extremely high volume, but it may lead to database integrity issues to do so.

        During validation, if filename is present and file_id is not, then file_id will be populated according to the
        filename. If both are populated, then the file_id will be validated to match the filename. The provided pattern
        set must contain 'file_id' and/or 'filename' columns as well as ['series', 'left', 'right', 'label'].
        :return: None
        """

        if validate:

            if 'file_id' not in df.columns and 'filename' not in df.columns:
                raise Exception('Pattern set must have either a file_id or filename column. Neither was found.')

            required_columns = ['series', 'left', 'right', 'label']
            if not all(c in df.columns for c in required_columns):
                raise Exception(f"Pattern set is missing one of the following required columns: [{', '.join(required_columns)}]")

            # Add optional columns if not present
            if 'file_id' not in df.columns:
                df['file_id'] = None
            if 'top' not in df.columns:
                df['top'] = None
            if 'bottom' not in df.columns:
                df['bottom'] = None

            # Reset index (so row number corresponds to index)
            df.reset_index(drop=True, inplace=True)

            # We'll do a validation and/or file_id fill-in if the filename column is present
            checkfn = 'filename' in df.columns

            for i in range(df.shape[0]):
                row = df.loc[i]
                fid = row['file_id']
                series = row['series']
                left = row['left']
                right = row['right']

                # These columns might be NaN (which evaluates to truthy), so override them to None
                if pd.isnull(fid):
                    fid = None
                if pd.isnull(left):
                    left = None
                if pd.isnull(right):
                    right = None

                # Check filename
                if checkfn and row['filename']:
                    fn = row['filename']
                    f = self.projparent.getFileByFilename(fn)
                    if not f:
                        # If they provided a filename but the file wasn't found in the project, raise an exception.
                        raise Exception(f"File {fn} not found in the project.")
                    if fid:
                        # If they provided both file_id and filename but they don't match, raise an exception.
                        if f.id != fid:
                            raise Exception(f"File ID {f.id} for filename {fn} did not match the provided file_id {fid}.")
                    else:
                        # File ID not provided, so populate it.
                        df.at[i, 'file_id'] = f.id
                    # Note: If the file_id was provided and filename was not provided, we don't care, as the
                    # filename column will be dropped.

                # If file_id is still not populated for any reason, we have a problem
                fid = df.at[i, 'file_id']
                if not fid or pd.isnull(fid):
                    raise Exception(f"File ID not found for {row}.")

                # Validate the file ID
                f = self.projparent.getFile(fid)
                if not f:
                    raise Exception(f"File ID {fid} not found for {row}.")

                # Check series name
                # TODO(gus, vedant): Check series name, but the file loading issue has to be resolved first.
                if not series:# or not f.getSeries(series):
                    raise Exception(f"Series {series} not found for {row}.")

                # Check left & right
                if not left or not right:
                    raise Exception(f"Left or right not found for {row}.")

        # Subset only the columns we need from the user
        df = df[['file_id', 'series', 'left', 'right', 'top', 'bottom', 'label']]

        # Add the project ID
        df.insert(0, "project_id", [self.projparent.id]*df.shape[0])

        # Add the id of this pattern set
        df.insert(0, "pattern_set_id", [self.id]*df.shape[0])

        # Do the db insert
        df.to_sql('patterns', models.db.engine, index=False, if_exists='append')

        # Refresh & update count
        self.refresh()

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
        self.refresh()
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
        self.refresh()
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

    def setDescription(self, description: str):
        """Set the pattern set's description."""
        self.dbmodel.description = description
        models.db.session.commit()

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

    def refresh(self):
        """
        Refresh model & update the count of patterns belonging to this set
        (this is normally an internally-used method).
        """
        models.db.session.refresh(self.dbmodel)
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