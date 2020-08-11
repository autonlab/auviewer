import os

from .config import config
from flask_login import current_user

from . import models

class AnnotationSet:

    def __init__(self, fileparent):

        # Set the file parent
        self.fileparent = fileparent

    def createAnnotation(self, left=None, right=None, top=None, bottom=None, seriesID='', label=''):

        newann = models.Annotation(
            user_id=current_user.id,
            project=self.fileparent.projparent.name,
            filepath=self.fileparent.getFilepath()[len(str(config['projectsDirPathObj'])):],
            series=seriesID,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            annotation=label)
        models.db.session.add(newann)
        models.db.session.commit()

        return newann.id

    # Deletes the annotation with the given ID, after some checks. Returns true
    # or false to indicate success.
    def deleteAnnotation(self, id):

        # Get the annotation in question
        annotationToDelete = models.Annotation.query.filter_by(id=id).first()

        # Verify the user has requested to delete his or her own annotation.
        if annotationToDelete.user_id != current_user.id:
            print("Error/securityissue on annotation deletion: User (id "+str(current_user.id)+") tried to delete an annotation (id "+str(id)+") belonging to another user (id "+str(annotationToDelete.user_id)+").")
            return False

        # Having reached this point, delete the annotation
        models.db.session.delete(annotationToDelete)
        models.db.session.commit()

        # Return true to indicate success
        return True

    # Returns a NumPy array of the annotations, or an empty list.
    def getAnnotations(self):

        # If we're in realtime, annotations are not available.
        if self.fileparent.mode() == 'realtime':
            return []

        return [[a.id, os.path.basename(a.filepath), a.series, a.left, a.right, a.top, a.bottom, a.annotation] for a in models.Annotation.query.filter_by(user_id=current_user.id, project=self.fileparent.projparent.name, filepath=self.fileparent.getFilepath()[len(str(config['projectsDirPathObj'])):]).all()]

    def updateAnnotation(self, id, left=None, right=None, top=None, bottom=None, seriesID='', label=''):

        # Get the annotation in question
        annotationToUpdate = models.Annotation.query.filter_by(id=id).first()

        # Verify the user has requested to update his or her own annotation.
        if annotationToUpdate.user_id != current_user.id:
            print("Error/securityissue on annotation update: User (id " + str(current_user.id) + ") tried to update an annotation (id " + str(id) + ") belonging to another user (id " + str(annotationToUpdate.user_id) + ").")
            return False

        # Set updated values
        annotationToUpdate.series = seriesID
        annotationToUpdate.left=left
        annotationToUpdate.right=right
        annotationToUpdate.top=top
        annotationToUpdate.bottom=bottom
        annotationToUpdate.annotation=label

        # Commit the changes
        models.db.session.commit()

        # Return true to indicate success
        return True
