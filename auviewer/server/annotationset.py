import os

from . import config
from flask_login import current_user

from . import dbgw

class AnnotationSet:

    def __init__(self, fileparent):

        # Set the file parent
        self.fileparent = fileparent

        self.anndb = dbgw.receive('Annotation')
        self.db=dbgw.receive('db')

    def createAnnotation(self, xBoundLeft=None, xBoundRight=None, yBoundTop=None, yBoundBottom=None, seriesID='', label=''):

        # We expect the filepath to begin with the projects directory
        if not self.fileparent.getFilepath().startswith(config.projectsDir):
            print(
                "Error on creating annotation. The file path is expected to start with the projects directory. File path:",
                self.fileparent.getFilepath(), "Projects directory:", config.projectsDir)
            return

        newann = self.anndb(
            user_id=current_user.id,
            project=self.fileparent.projparent.name,
            filepath=self.fileparent.getFilepath()[len(config.projectsDir):],
            series=seriesID,
            xboundleft=xBoundLeft,
            xboundright=xBoundRight,
            yboundtop=yBoundTop,
            yboundbottom=yBoundBottom,
            annotation=label)
        self.db.session.add(newann)
        self.db.session.commit()

        return newann.id

    # Deletes the annotation with the given ID, after some checks. Returns true
    # or false to indicate success.
    def deleteAnnotation(self, id):

        # Get the annotation in question
        annotationToDelete = self.anndb.query.filter_by(id=id).first()

        # Verify the user has requested to delete his or her own annotation.
        if annotationToDelete.user_id != current_user.id:
            print("Error/securityissue on annotation deletion: User (id "+str(current_user.id)+") tried to delete an annotation (id "+str(id)+") belonging to another user (id "+str(annotationToDelete.user_id)+").")
            return False

        # Having reached this point, delete the annotation
        self.db.session.delete(annotationToDelete)
        self.db.session.commit()

        # Return true to indicate success
        return True

    # Returns a NumPy array of the annotations, or an empty list.
    def getAnnotations(self):

        # If we're in realtime, annotations are not available.
        if self.fileparent.mode() == 'realtime':
            return []

        # We expect the filepath to begin with the projects directory
        if not self.fileparent.getFilepath().startswith(config.projectsDir):
            print("Error on getting annotations. The file path is expected to start with the projects directory. File path:", self.fileparent.getFilepath(), "Projects directory:", config.projectsDir)
            return []

        return [[a.id, os.path.basename(a.filepath), a.series, a.xboundleft, a.xboundright, a.yboundtop, a.yboundbottom, a.annotation] for a in self.anndb.query.filter_by(user_id=current_user.id, project=self.fileparent.projparent.name, filepath=self.fileparent.getFilepath()[len(config.projectsDir):]).all()]

    def updateAnnotation(self, id, xBoundLeft=None, xBoundRight=None, yBoundTop=None, yBoundBottom=None, seriesID='', label=''):

        # Get the annotation in question
        annotationToUpdate = self.anndb.query.filter_by(id=id).first()

        # Verify the user has requested to update his or her own annotation.
        if annotationToUpdate.user_id != current_user.id:
            print("Error/securityissue on annotation update: User (id " + str(current_user.id) + ") tried to update an annotation (id " + str(id) + ") belonging to another user (id " + str(annotationToUpdate.user_id) + ").")
            return False

        # Verify the annotation ID belongs to the file it should
        if annotationToUpdate.filepath != self.fileparent.getFilepath():
            print("Error on annotation update: File passed in did not match file of annotation. Annotation ID " + str(id) + ", file specified in request '" + self.fileparent.getFilepath() + "', file listed in annotation '" + str(annotationToUpdate.filepath) + "'.")
            return False

        # Set updated values
        annotationToUpdate.series = seriesID
        annotationToUpdate.xboundleft=xBoundLeft
        annotationToUpdate.xboundright=xBoundRight
        annotationToUpdate.yboundtop=yBoundTop
        annotationToUpdate.yboundbottom=yBoundBottom
        annotationToUpdate.annotation=label

        # Commit the changes
        self.db.session.commit()

        # Return true to indicate success
        return True
