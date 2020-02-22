import config
from file import File
import os
from exceptions import ProcessedFileExists

class Project:

    # The project name should also be the directory name in the originals dir.
    def __init__(self, project_name):

        self.name = project_name
        
        # Set the project root directory
        self.project_dir = os.path.join(config.projectsDir, self.name)
        
        # Set the project templates directory
        self.templates_dir = os.path.join(self.project_dir, 'templates')
        
        # Set the project interface templates directory
        self.interface_templates_dir = os.path.join(self.templates_dir, 'interfaces')

        # Set the project original files directory
        self.originals_dir = os.path.join(self.project_dir, 'originals')
        
        # Set the project processed files directory
        self.processed_dir = os.path.join(self.project_dir, 'processed')
        
        # Holds references to the files that belong to the project
        self.files = []
        
    def getFile(self, filename):

        # TODO(gus): Convert this to a hash table
        for f in self.files:
            if f.filename == filename:
                return f

        # Having reached this point, we cannot find the file
        return None
    
    def getInitialPayloadOutput(self):
        
        print("Assembling initial project payload output for project", self.name)
        
        outputObject = {
            'name': self.name,
            'files': self.getProcessedFileList(),
            'project_template': self.getProjectTemplate(),
            'interface_templates': self.getInterfaceTemplates()
        }
        
        # Return the output object
        return outputObject

    # Returns string containing the interface templates JSON, or None if it does
    # not exist.
    def getInterfaceTemplates(self):
    
        try:
            with open(os.path.join(self.templates_dir, 'interface_templates.json'), 'r') as f:
                return f.read()
    
        except:
            return None

    def getProcessedFileList(self):

        response = []

        for filename in os.listdir(self.originals_dir):
            if filename.endswith(".h5") and os.path.isfile(os.path.join(self.processed_dir, os.path.splitext(filename)[0] + '_processed.h5')):
                response.append(filename)

        # Sort the list alphabetically
        response.sort()

        return response
    
    # Returns string containing the project template JSON, or None if it does
    # not exist.
    def getProjectTemplate(self):
    
        try:
            with open(os.path.join(self.templates_dir, 'project_template.json'), 'r') as f:
                return f.read()
            
        except:
            return None

    def getUnprocessedFileList(self):

        response = []

        for filename in os.listdir(self.originals_dir):
            if filename.endswith(".h5") and not os.path.isfile(os.path.join(self.processed_dir, os.path.splitext(filename)[0] + '_processed.h5')):
                response.append(filename)

        # Sort the list alphabetically
        response.sort()

        return response

    # Loads the file corresponding to the provided filename, adds it to the list
    # of loaded project files, and returns the File instance. If opening the
    # file fails, None object will be returned.
    def loadProcessedFile(self, filename):

        try:
            self.files.append(File(self, filename))
            return self.files[len(self.files) - 1]

        except Exception as e:
            print("Opening/instantiating file " + filename + " failed with the following exception.\n", e)
            return None

    def loadProcessedFiles(self):

        for f in self.getProcessedFileList():
            self.loadProcessedFile(f)
            break

    # Iterates through all unprocessed files and processes each one. Supports
    # multi-process batch processing in a "pretty good" way that relies on the
    # file system to avoid collisions. This is not a guarantee like there could
    # be with inter-process communication.
    def processFiles(self):
        
        # Iterate through the unprocessed files and process each one.
        for f in self.getUnprocessedFileList():
            
            try:
                
                # Process the file
                File(self, f)
                # file = File(f[0], f[1])
                # self.files.append(file)
            
            # If the processed file is found to already exist (in the case of
            # multiple running processes), skip this file. This supports multi-
            # process batch processing, though it does not guarantee against
            # collision since there is no inter-process communication.
            except ProcessedFileExists:
                
                print("The processed file was found to already exist. Skipping this file.")