"""Class and related functionality for projects."""
import logging
import pandas as pd
import traceback

from pathlib import Path
from sqlalchemy import and_
from sqlalchemy.orm import contains_eager
from typing import List, Dict, Optional

from . import models
from .patternset import PatternSet
from .config import config
from .file import File
from .shared import annotationOrPatternOutput, createEmptyJSONFile

# Will hold loaded projects
loadedProjects = []

class Project:
    """Represents an auviewer project."""

    def __init__(self, projectModel, processNewFiles=True):
        """The project name should also be the directory name in the projects directory."""

        # Set id, name, and relevant paths
        self.id = projectModel.id
        self.name = projectModel.name
        self.projDirPathObj = Path(projectModel.path)
        self.originalsDirPathObj = self.projDirPathObj / 'originals'
        self.processedDirPathObj = self.projDirPathObj / 'processed'

        # Hold a reference to the db model for future use
        self.model = projectModel

        # Load interface templates
        self.interfaceTemplates = "{}"
        p = self.projDirPathObj / 'templates' / 'interface_templates.json'
        if p.is_file():
            with p.open() as f:
                self.interfaceTemplates = f.read()

        # Load project template
        self.projectTemplate = "{}"
        p = self.projDirPathObj / 'templates' / 'project_template.json'
        if p.is_file():
            with p.open() as f:
                self.projectTemplate = f.read()

        # Holds references to the files that belong to the project
        self.files = []

        # Holds references to the pattern sets that belong to the project,
        # indexed by pattern set ID.
        self.patternsets = {}

        # Load project files
        self.loadProjectFiles(processNewFiles)

        # Load pattern sets
        for psm in models.PatternSet.query.filter_by(project_id=self.id).all():
            self.patternsets[psm.id] = PatternSet(self, psm)

    def __del__(self):
        """Cleanup"""
        try:
            self.observer.join()
        except:
            pass

    def createPatternSet(self, name: str, description=None) -> PatternSet:
        """
        Create and return a new pattern set.
        :returns: a new PatternSet instance
        """

        # Create pattern set in the database
        patternSetModel = models.PatternSet(project_id=self.id, name=name, description=description)
        models.db.session.add(patternSetModel)
        models.db.session.commit()

        # Instantiate PatternSet and add to the project's pattern sets
        ps = PatternSet(self, patternSetModel)
        self.patternsets[ps.id] = ps

        # Return the pattern set
        return ps

    def detectPatterns(self, type, series, thresholdlow, thresholdhigh, duration, persistence, maxgap):
        """Run pattern detection on all files, and return a single list of results."""
        patterns = [[f.id, f.name, series, pattern[0], pattern[1], None, None] for f in self.files for pattern in f.detectPatterns(type, series, thresholdlow, thresholdhigh, duration, persistence, maxgap)]
        return pd.DataFrame(patterns, columns=['file_id', 'filename', 'series', 'left', 'right', 'top', 'bottom'])

    def getAnnotationsOutput(self, user_id):
        """Returns a list of user's annotations for all files in the project"""
        return [[a.id, a.file_id, Path(a.file.path).name, a.series, a.left, a.right, a.top, a.bottom, a.label, a.pattern_id] for a in models.Annotation.query.filter_by(user_id=user_id, project_id=self.id).all()]

    def getFile(self, id):
        """Returns the file with matching ID or None."""
        for f in self.files:
            if f.id == id:
                return f
        return None

    def getInitialPayload(self, user_id):
        """Returns initial project payload data"""

        print("Assembling initial project payload output for project", self.name)

        return {

            # Project data
            'project_id': self.id,
            'project_name': self.name,
            'project_assignments': [{
                'id': ps.id,
                'name': ps.name,
                'description': ps.description,
                'patterns': [
                    #annotationOrPatternOutput(p) for p in ps.patterns
                    annotationOrPatternOutput(p, p.annotations[0] if len(p.annotations)>0 else None) for p in models.db.session.query(models.Pattern).filter_by(pattern_set_id=ps.id).outerjoin(models.Annotation, and_(models.Annotation.pattern_id==models.Pattern.id, models.Annotation.user_id==user_id)).options(contains_eager('annotations')).all()
                ]
            } for ps in models.PatternSet.query.filter(models.PatternSet.users.any(id=user_id), models.PatternSet.project_id==self.id).all()],
            'project_files': [[f.id, f.origFilePathObj.name] for f in self.files],

            # Template data
            'builtin_default_interface_templates': config['builtinDefaultInterfaceTemplates'],
            'builtin_default_project_template': config['builtinDefaultProjectTemplate'],
            'global_default_interface_templates': config['globalDefaultInterfaceTemplates'],
            'global_default_project_template': config['globalDefaultProjectTemplate'],
            'interface_templates': self.interfaceTemplates,
            'project_template': self.projectTemplate,

        }

    def getPatternSets(self) -> Dict[int, PatternSet]:
        """
        Get project's pattern sets.
        :returns: a dict of the project's PatternSet instances, indexed by id
        """
        return self.patternsets

    def getPatternSetByID(self, id) -> Optional[PatternSet]:
        """
        Get project's pattern set by ID.
        :returns: the PatternSet instance belonging to the id, or None if not found
        """
        return self.patternsets[id] if id in self.patternsets else None

    def getTotalPatternCount(self) -> int:
        """
        Get total count of patterns in all the project's pattern sets
        :returns: number of patterns
        """
        return sum([ps.count for ps in self.patternsets.values()])

    def loadProjectFiles(self, processNewFiles=True):
        """Load files belonging to the project, and process new files if desired."""

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
            for newOrigFilePathObj in [p for p in self.originalsDirPathObj.iterdir() if p.is_file() and p.suffix == '.h5' and not any(map(lambda existingFilePathObj: p.samefile(existingFilePathObj), existingFilePathObjs))]:

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

def getProjectByID(id) -> Optional[PatternSet]:
    """
    Returns the project with matching ID.
    :returns: the Project instance belonging to the id, or None if not found
    """
    global loadedProjects
    for p in loadedProjects:
        if p.id == id:
            return p
    return None

def getProjectsPayload(user_id) -> List[Dict]:
    """
    Returns a list of project information accessible to a given user.
    :returns: list of objects containing project information
    """
    global loadedProjects
    return [{
        'id': p.id,
        'name': p.name,
        'files': len(p.files),
        'patterns': p.getTotalPatternCount(),
        'annotations': models.Annotation.query.filter_by(user_id=user_id, project_id=p.id).count(),
        'assignments_rem': models.User.query.filter_by(id=user_id).first().assignments_remaining,
    } for p in loadedProjects]

def loadProjects() -> None:
    """
    Load or reload projects into memory. This must be called before getProjectByID
    and list_projects. Will also detect new projects in the projects folder and
    add them to the database.
    :return: list of Project instances
    """

    global loadedProjects

    logging.info("Loading projects.")

    # Reset projects to empty list
    loadedProjects = []

    # Load projects from the database
    projs = models.Project.query.all()
    for p in projs:

        logging.info(f"Loading project id {p.id} ({p.name}) at {p.path}")

        # Path object for the project
        projDirPathObj = Path(p.path)

        # Validate the project folder
        try:
            validateProjectFolder(projDirPathObj)
        except Exception as e:
            logging.error(f'Project folder {projDirPathObj} is invalid.\n{e}\n{traceback.format_exc()}')
            # TODO(gus): Update the database to reflect this?
        else:
            # TODO(gus): We need to have project take absolute path and project name!
            # Instantiate project, and add to the list to be returned
            loadedProjects.append(Project(p))

            logging.info("Finished loading project.")

    # Detect new project folders not in the database
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
            validateProjectFolder(projDirPathObj)
        except Exception as e:
            logging.error(f"Project folder {projDirPathObj} is invalid.\n{e}\n{traceback.format_exc()}")
        else:
            logging.info(f'Project folder {projDirPathObj} is valid.')

            # Scaffold project folder
            scaffoldProjectFolder(projDirPathObj)

            # Add project to the database
            project = models.Project(name=projDirPathObj.name, path=str(projDirPathObj.resolve()))
            models.db.session.add(project)
            models.db.session.commit()
            logging.info(f"Added project to database: {projDirPathObj}")

            # TODO(gus): We need to have project take absolute path and project name!
            # Instantiate project, and add to the list to be returned
            loadedProjects.append(Project(project))

    logging.info("Finished loading projects.")

# Generate the baseline project folder contents as needed
def scaffoldProjectFolder(projDirPathObj):

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
def validateProjectFolder(projDirPathObj):

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