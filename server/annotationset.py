import h5py
import numpy as np
from flask_login import current_user
from pprint import pprint
import dbgw

class AnnotationSet:
    
    def __init__(self, fileparent):
        
        # Set the file parent
        self.fileparent = fileparent
        
        self.anndb = dbgw.receive('Annotation')
        self.db=dbgw.receive('db')

    def createAnnotation(self, xBoundLeft=None, xBoundRight=None, yBoundTop=None, yBoundBottom=None, seriesID='', label=''):
    
        newann = self.anndb(
            user_id=current_user.id,
            filepath=self.fileparent.getFilepath(),
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
        
        # Verify the annotation ID belongs to the file it should
        if annotationToDelete.filepath != self.fileparent.getFilepath():
            print("Error on annotation deletion: File passed in did not match file of annotation. Annotation ID "+str(id)+", file specified in request '"+self.fileparent.getFilepath()+"', file listed in annotation '"+str(annotationToDelete.filepath)+"'.")
            return False
        
        # Having reached this point, delete the annotation
        self.db.session.delete(annotationToDelete)
        self.db.session.commit()
        
        # Return true to indicate success
        return True
        
    # Returns a NumPy array of the annotations, or an empty list.
    def getAnnotations(self):
        
        return [[a.id, a.xboundleft, a.xboundright, a.yboundtop, a.yboundbottom, a.annotation] for a in self.anndb.query.filter_by(user_id=current_user.id, filepath=self.fileparent.getFilepath()).all()]
    
    # Returns the annotations dataset or None if it cannot be retrieved. If the
    # annotations dataset does not exist in the processed file, it will create
    # a new one and return it.
    def getAnnotationsDataset(self):
    
        # Get the processed file
        pf = self.fileparent.getProcessedFile()
    
        # Handle case where we cannot retrieve processed file
        if pf is None:
            print("Unable to add annotation because processed file could not be retrieved.")
            return None
        
        # Attempt to retrieve the annotations dataset
        dset = pf.get('annotations')
        
        # If the dataset was found, return it
        if dset is not None:
            return dset

        # Otherwise, create the annotations dataset and return it
        return pf.create_dataset("annotations", (0,), maxshape=(None,), dtype=[('xboundleft', 'float64'), ('xboundright', 'float64'), ('yboundtop', 'float64'), ('yboundbottom', 'float64'), ('userid', h5py.special_dtype(vlen=str)), ('seriesid', h5py.special_dtype(vlen=str)), ('label', h5py.special_dtype(vlen=str))])

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
        annotationToUpdate.xboundleft=xBoundLeft
        annotationToUpdate.xboundright=xBoundRight
        annotationToUpdate.yboundtop=yBoundTop
        annotationToUpdate.yboundbottom=yBoundBottom
        annotationToUpdate.annotation=label

        # Commit the changes
        self.db.session.commit()

        # Return true to indicate success
        return True