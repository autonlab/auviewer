import config
from file import File
import os
from exceptions import ProcessedFileExists

class Project:

    def __init__(self):

        # Holds references to the files that belong to the project
        self.files = []
        
    def getFile(self, filename):

        # TODO(gus): Convert this to a hash table
        for f in self.files:
            if f.filename == filename:
                return f

        # Having reached this point, we cannot find the file
        return None

    def getActiveFileList(self):

        response = []

        for filename in os.listdir(config.originalFilesDir):
            if filename.endswith(".h5") and os.path.isfile(os.path.join(config.processedFilesDir, os.path.splitext(filename)[0] + '_processed.h5')):
                response.append([filename, config.originalFilesDir])

        # Sort the list alphabetically
        response.sort()

        return response

    def getActiveFileListOutput(self):
        r = [list(i) for i in zip(*self.getActiveFileList())]
        if len(r) > 0:
            return r[0]
        else:
            return []

    def getUnprocessedFileList(self):

        response = []

        for filename in os.listdir(config.originalFilesDir):
            if filename.endswith(".h5") and not os.path.isfile(os.path.join(config.processedFilesDir, os.path.splitext(filename)[0] + '_processed.h5')):
                response.append([filename, config.originalFilesDir])

        # Sort the list alphabetically
        response.sort()

        return response

    def loadProcessedFiles(self):

        for f in self.getActiveFileList():
            file = File(f[0], f[1])
            self.files.append(file)

    # Iterates through all unprocessed files and processes each one. Supports
    # multi-process batch processing in a "pretty good" way that relies on the
    # file system to avoid collisions. This is not a guarantee like there could
    # be with inter-process communication.
    def processFiles(self):
        
        # Iterate through the unprocessed files and process each one.
        for f in self.getUnprocessedFileList():
            
            try:
                
                # Process the file
                File(f[0], f[1])
                # file = File(f[0], f[1])
                # self.files.append(file)
            
            # If the processed file is found to already exist (in the case of
            # multiple running processes), skip this file. This supports multi-
            # process batch processing, though it does not guarantee against
            # collision since there is no inter-process communication.
            except ProcessedFileExists:
                
                print("The processed file was found to already exist. Skipping this file.")