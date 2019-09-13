import h5py
import numpy as np
from flask_login import current_user
from pprint import pprint

class AnnotationSet:
    
    def __init__(self, fileparent):
        
        # Set the file parent
        self.fileparent = fileparent
        
    # Returns a NumPy array of the annotations, or an empty list.
    def getAnnotations(self):
        
        pprint(vars(current_user))

        # Grab the user ID
        userID = current_user.email

        # We expect a non-empty user ID to be present
        if len(userID) < 1:
            print("User ID was not found in getAnnotations.")
            return []
        
        adset = self.getAnnotationsDataset()
        
        if adset is None:
            return []
        else:
    
            # Return results filtered for only the user's annotations
            bset = adset[()]
            print('here: ', bset[bset['userid']==userID])
            return bset[bset['userid']==userID]
    
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

    def writeAnnotation(self, xBoundLeft=None, xBoundRight=None, yBoundTop=None, yBoundBottom=None, seriesID='', label=''):
    
        # If a series ID is specified but does not exist, we cannot proceed.
        if len(seriesID) > 0 and self.fileparent.getSeries(seriesID) is None:
            print("Unable to write annotation because the series ID specified is not found.")
            return

        # Grab the user ID
        userID = current_user.email

        # We expect a non-empty user ID to be present
        if len(userID) < 1:
            print("User ID was not found in writeAnnotation.")
            return
    
        # Get the annotations dataset for the processed data file for writing
        adset = self.getAnnotationsDataset()
    
        # Handle the case where we were not able to get the annotations dataset
        if adset is None:
            print("Unable to write annotation because the annotations dataset could not be retrieved.")
            return
        
        # Assemble the recarray which we'll add to the annotations dataset
        ra = np.recarray((1,), dtype=[('xboundleft', 'float64'), ('xboundright', 'float64'), ('yboundtop', 'float64'), ('yboundbottom', 'float64'), ('userid', h5py.special_dtype(vlen=str)), ('seriesid', h5py.special_dtype(vlen=str)), ('label', h5py.special_dtype(vlen=str))])

        ra[0].xboundleft = xBoundLeft
        ra[0].xboundright = xBoundRight
        ra[0].yboundtop = yBoundTop
        ra[0].yboundbottom = yBoundBottom
        ra[0].userid = userID
        ra[0].seriesid = seriesID
        ra[0].label = label
    
        # Add a row to the annotations dataset
        adset.resize(adset.shape[0] + 1, axis=0)
    
        # Write the annotation
        adset[-1] = ra