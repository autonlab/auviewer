import os
import time
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask_login import current_user

from . import config
from . import dbgw
from .file import File
from .exceptions import ProcessedFileExists

class FileChangeHandler(FileSystemEventHandler):

    def __init__(self, target_project):
        self.target_project = target_project

    def on_created(self, event):

        if event.is_directory:
            return

        # Wait a beat (for both original and processed to be moved)
        time.sleep(2)

        print("Detected change:", event.src_path)

        # If the file has been loaded, reload it.
        newfilename = os.path.basename(event.src_path)
        for f in self.target_project.files:
            if newfilename == f.orig_filename:
                print("Reloading", newfilename)
                self.target_project.files.remove(f)
                self.target_project.loadProcessedFile(newfilename)


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

        self.anndb = dbgw.receive('Annotation')
        self.db = dbgw.receive('db')

    # Cleanup
    def __del__(self):
        try:
            self.observer.join()
        except:
            pass

    # Returns a list of user's annotations for all files in the project
    def getAnnotations(self):

        return [[a.id, os.path.basename(a.filepath), a.series, a.xboundleft, a.xboundright, a.yboundtop, a.yboundbottom, a.annotation] for a in self.anndb.query.filter_by(user_id=current_user.id, project=self.name).all()]

    def getAvailableFilesList(self):
        return [f.orig_filename for f in self.files]

    def getFile(self, filename):

        # TODO(gus): Convert this to a hash table
        for f in self.files:
            if f.orig_filename == filename:
                return f

        # Having reached this point, we cannot find the file
        return None

    def getInitialPayloadOutput(self):

        print("Assembling initial project payload output for project", self.name)

        outputObject = {
            'name': self.name,
            'files': self.getAvailableFilesList(),
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

        try:

            for filename in os.listdir(self.originals_dir):
                if filename.endswith(".h5") and os.path.isfile(os.path.join(self.processed_dir, os.path.splitext(filename)[0] + '_processed.h5')):
                    response.append(filename)

        except Exception as e:

            print("Listing processed project files failed.", e)

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

        try:

            for filename in os.listdir(self.originals_dir):
                if filename.endswith(".h5") and not os.path.isfile(os.path.join(self.processed_dir, os.path.splitext(filename)[0] + '_processed.h5')):
                    response.append(filename)

        except Exception as e:

            print("Listing unprocessed project files failed.", e)

        # Sort the list alphabetically
        response.sort()

        return response

    # Loads the file corresponding to the provided filename, adds it to the list
    # of loaded project files, and returns the File instance. If opening the
    # file fails, None object will be returned.
    def loadProcessedFile(self, orig_filename):

        try:

            proc_filename = os.path.splitext(orig_filename)[0] + '_processed.h5'

            self.files.append(File(
                projparent=self,
                orig_filename=orig_filename,
                proc_filename=proc_filename,
                orig_dir=self.originals_dir,
                proc_dir=self.processed_dir
            ))
            return self.files[len(self.files) - 1]

        except Exception as e:

            print("Opening/instantiating original file " + orig_filename + " and processed file " + proc_filename + " failed with the following exception.\n", traceback.format_exc())
            return None

    def loadProcessedFiles(self):

        # i=0
        for orig_filename in self.getProcessedFileList():
            self.loadProcessedFile(orig_filename)
            # break
            # i = i + 1
            # if i == 5:
            #     break

        # Establish a process to watch for updated versions of any project files
        if os.path.isdir(self.originals_dir):
            file_change_handler = FileChangeHandler(self)
            self.observer = Observer()
            self.observer.schedule(file_change_handler, self.originals_dir)
            self.observer.start()

    # Iterates through all unprocessed files and processes each one. Supports
    # multi-process batch processing in a "pretty good" way that relies on the
    # file system to avoid collisions. This is not a guarantee like there could
    # be with inter-process communication.
    def processFiles(self):

        # Iterate through the unprocessed files and process each one.
        for orig_filename in self.getUnprocessedFileList():

            try:

                # Process the file
                proc_filename = os.path.splitext(orig_filename)[0] + '_processed.h5'
                File(
                    projparent=self,
                    orig_filename=orig_filename,
                    proc_filename=proc_filename,
                    orig_dir=self.originals_dir,
                    proc_dir=self.processed_dir
                )

            # If the processed file is found to already exist (in the case of
            # multiple running processes), skip this file. This supports multi-
            # process batch processing, though it does not guarantee against
            # collision since there is no inter-process communication.
            except ProcessedFileExists:

                print("The processed file was found to already exist. Skipping this file.")
