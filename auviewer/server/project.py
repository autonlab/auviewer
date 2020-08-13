"""Class and related functionality for projects."""
import logging
import os
import traceback

from flask_login import current_user
from pathlib import Path

from . import models
from .config import config
from .file import File
from .shared import createEmptyJSONFile

class Project:

    # The project name should also be the directory name in the projects directory.
    def __init__(self, id, name, projDirPathObj, processNewFiles=True):

        # Set id, name, and relevant paths
        self.id = id
        self.name = name
        self.projDirPathObj = projDirPathObj
        self.originalsDirPathObj = projDirPathObj / 'originals'
        self.processedDirPathObj = projDirPathObj / 'processed'
        self.templatesDirPathObj = projDirPathObj / 'templates'
        self.interfaceTemplatesFilePathObj = self.templatesDirPathObj / 'interface_templates.json'
        self.projectTemplateFilePathObj = self.templatesDirPathObj / 'project_template.json'

        # Holds references to the files that belong to the project
        self.files = []

        # Load project files
        self.loadProjectFiles(processNewFiles)

    # Cleanup
    def __del__(self):
        try:
            self.observer.join()
        except:
            pass

    # Returns a list of user's annotations for all files in the project
    def getAnnotations(self):

        return [[a.id, os.path.basename(a.filepath), a.series, a.left, a.right, a.top, a.bottom, a.annotation] for a in models.Annotation.query.filter_by(user_id=current_user.id, project=self.name).all()]

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
            with self.interfaceTemplatesFilePathObj.open() as f:
                return f.read()
        except:
            return None

    # Returns string containing the project template JSON, or None if it does
    # not exist.
    def getProjectTemplate(self):
        try:
            with self.projectTemplateFilePathObj.open() as f:
                return f.read()
        except:
            return None

    # Load files belonging to the project, and process new files if desired.
    def loadProjectFiles(self, processNewFiles=True):

        # Will hold all project files that exist in the database (in order to
        # detect new files to process).
        existingFilePathObjs = []

        # Get all of the project's files listed in the database
        fileDBModels = models.File.query.filter_by(project_id=self.id).all()

        # For each project file in the database...
        for fileDBModel in fileDBModels:

            # Verify the original file exists on the file system
            origFilePathObj = Path(fileDBModel.path)
            existingFilePathObjs.append(origFilePathObj)
            if not origFilePathObj.exists():
                logging.error(
                    f"File ID {fileDBModel.id} in the database is missing the original file on the file system at {fileDBModel.path}")
                continue
                # TODO(gus): Do something else with this? Like set error state in the database entry and display in GUI?

            # Verify the processed file exists on the file system
            procFilePathObj = self.processedDirPathObj / (origFilePathObj.stem + '_processed.h5')
            if not procFilePathObj.exists():
                logging.error(
                    f"File ID {fileDBModel.id} in the database is missing the processed file on the file system at {procFilePathObj}")
                continue
                # TODO(gus): Do something else with this? Like set error state in the database entry and display in GUI?

            # Instantiate the file class, and attach to this project instance
            self.files.append(File(self, fileDBModel.id, origFilePathObj, procFilePathObj, processNewFiles))

        # If processNewFiles is true, then go through and process new files
        if processNewFiles:

            # For each new project file which does not exist in the database...
            for newOrigFilePathObj in [p for p in self.originalsDirPathObj.iterdir() if
                                       p.is_file() and p.suffix == '.h5' and not any(
                                               map(lambda p: p.samefile(newOrigFilePathObj), existingFilePathObjs))]:

                # Establish the path of the new processed file
                newProcFilePathObj = self.processedDirPathObj / (newOrigFilePathObj.stem + '_processed.h5')

                # Instantiate the file class with an id of -1, and attach to
                # this project instance.
                try:
                    newFileClassInstance = File(self, -1, newOrigFilePathObj, newProcFilePathObj, processNewFiles)
                except Exception as e:
                    logging.error(f"New file {newOrigFilePathObj} could not be processed.\n{e}\n{traceback.format_exc()}")
                    continue

                # Now that the processing has completed (if not, an exception
                # would have been raised), add the file to the database and
                # update the file class instance ID.
                newFileDBEntry = models.File(project_id=self.id, path=str(newOrigFilePathObj))
                models.db.session.add(newFileDBEntry)
                models.db.session.commit()

                # Update the file class instance ID, and add it to the files
                # list for this project.
                newFileClassInstance.id = newFileDBEntry.id
                self.files.append(newFileClassInstance)


def get_project(id):
    pass

# Load projects into memory. This must be called before get_project and
# list_projects. Will also detect new projects in the projects folder and add
# them to the database.
def load_projects():

    # Will hold loaded projects
    projectsList = []

    # Load projects from the database
    logging.info("Loading projects from the database.")
    projs = models.Project.query.all()
    logging.info("Projects in database:")
    for p in projs:
        logging.info(f'{p.id} / {p.name} / {p.path}')

        # Path object for the project
        projDirPathObj = Path(p.path)

        # Validate the project folder
        try:
            validate_project_folder(projDirPathObj)
        except Exception as e:
            logging.error(f'Project folder {projDirPathObj} is invalid.\n{e}\n{traceback.format_exc()}')
            # TODO(gus): Update the database to reflect this?
        else:
            # TODO(gus): We need to have project take absolute path and project name!
            # Instantiate project, and add to the list to be returned
            projectsList.append(Project(p.id, p.name, Path(p.path)))

    # Detect new project folders not in the database
    logging.info(f"Scanning projects folder {config['projectsDirPathObj']} for new projects.")
    for projDirPathObj in [p for p in config['projectsDirPathObj'].iterdir() if p.is_dir()]:

        # Check whether path exists in database projects
        foundInExistingProject = False
        for p in projs:
            if Path(p.path).samefile(projDirPathObj):
                foundInExistingProject = True
                break

        # Skip if this project folder was found to exist in the database already
        if foundInExistingProject:
            continue

        logging.info(f"Found new project at {projDirPathObj}.")

        # Ensure we have a valid project folder (i.e. it can be empty, but it
        # cannot contain invalid files or folders).
        try:
            validate_project_folder(projDirPathObj)
        except Exception as e:
            logging.error(f"Project folder {projDirPathObj} is invalid.\n{e}\n{traceback.format_exc()}")
        else:
            logging.info(f'Project folder {projDirPathObj} is valid.')

            # Scaffold project folder
            scaffold_project_folder(projDirPathObj)

            # Add project to the database
            project = models.Project(name=projDirPathObj.name, path=str(projDirPathObj.resolve()))
            models.db.session.add(project)
            models.db.session.commit()
            logging.info(f"Added project to database: {projDirPathObj}")

            # TODO(gus): We need to have project take absolute path and project name!
            # Instantiate project, and add to the list to be returned
            projectsList.append(Project(project.id, project.name, Path(project.path)))

    logging.info(f"Loaded projects: {projectsList}")

    # Return the list of loaded projects
    return projectsList

# Generate the baseline project folder contents as needed
def scaffold_project_folder(projDirPathObj):

    logging.info(f"Scaffolding project folder {projDirPathObj}.")

    # Create the originals folder if needed
    (projDirPathObj / 'originals').mkdir(exist_ok=True)

    # Create the processed folder if needed
    (projDirPathObj / 'processed').mkdir(exist_ok=True)

    # Create the templates folder if needed
    projTemplatesFolderPathObj = projDirPathObj / 'templates'
    projTemplatesFolderPathObj.mkdir(exist_ok=True)

    # Create empty template files if needed
    createEmptyJSONFile(projTemplatesFolderPathObj / 'interface_templates.json')
    createEmptyJSONFile(projTemplatesFolderPathObj / 'project_template.json')

    logging.info(f"Finished scaffolding project folder {projDirPathObj}.")

# Raises an exception if the project folder is invalid
def validate_project_folder(projDirPathObj):

    logging.info(f"Validating project folder {projDirPathObj}.")

    # Validate top-level folders
    for p in [p for p in projDirPathObj.iterdir()]:

        # Project folder should only contain directories
        if not p.is_dir():
            raise Exception(f'Project folder contains invalid file: {p}')

        # Validate expected top-level folder names
        if p.name not in ['originals', 'processed', 'templates']:
            raise Exception(f'Project folder contains invalid folder: {p}')

    # Validate expected template files if they exist.
    tp = p / "templates"
    if tp.exists():
        for p in [p for p in tp.iterdir()]:
            if p.name not in ['project_template.json', 'interface_templates.json']:
                raise Exception(f'Project templates folder contains invalid file: {p}')

    # TODO(gus): Validate that originals have processed?

    logging.info(f'Finished validating project folder {projDirPathObj}.')












# The below was used for detecting file changes (e.g. new files, file replacements).

# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# class FileChangeHandler(FileSystemEventHandler):
#
#     def __init__(self, target_project):
#         self.target_project = target_project
#
#     def on_created(self, event):
#
#         if event.is_directory:
#             return
#
#         # Wait a beat (for both original and processed to be moved)
#         time.sleep(2)
#
#         print("Detected change:", event.src_path)
#
#         # If the file has been loaded, reload it.
#         newfilename = os.path.basename(event.src_path)
#         for f in self.target_project.files:
#             if newfilename == f.orig_filename:
#                 print("Reloading", newfilename)
#                 self.target_project.files.remove(f)
#                 self.target_project.loadProcessedFile(newfilename)

# # This was used to setup the file change listener on file load.
# # Establish a process to watch for updated versions of any project files
# if os.path.isdir(self.originals_dir):
#     file_change_handler = FileChangeHandler(self)
#     self.observer = Observer()
#     self.observer.schedule(file_change_handler, self.originals_dir)
#     self.observer.start()