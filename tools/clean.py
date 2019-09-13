import numpy as np
import h5py
import os

### DANGER - DELETES DATA - USE WITH EXTREME CAUTION
### This is a tool to batch delete a certain dataset from a directory of files.
### Uncomment the code to use it, but use with extreme caution.

# # Directory to pull h5 files from
# path = '/zfsauton/data/public/gwelter/processed/'
#
# # Name of the dataset to delete
# dsetname = 'annotations'
#
# # Go through all processed files
# for filename in os.listdir(path):
#
#     # Open the file
#     f = h5py.File(os.path.join(path, filename))
#
#     # Attempt to retrieve the annotations dataset
#     dset = f.get(dsetname)
#
#     if dset is None:
#         print(filename+': Prior to deletion, there was NO dataset.')
#     else:
#         print(filename+': Prior to deletion, there WAS a dataset.')
#
#     # If the dataset was found, delete it
#     if dset is not None:
#
#         # Delete the dataset
#         del f[dsetname]
#
#         # Attempt to retrieve the annotations dataset again (for checking)
#         dset = f.get(dsetname)
#
#         if dset is None:
#             print(filename+': After deletion, there was NO dataset.')
#         else:
#             print(filename+': After deletion, there WAS a dataset.')