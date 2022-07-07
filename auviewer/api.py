"""Python API for working with AUViewer."""

import sys
import logging
import traceback

from flask import Flask
from pathlib import Path
from typing import List, Dict, Optional
from pathlib import Path

from . import models
from .config import config, set_data_path
from .file import File
from .project import Project
from .shared import createEmptyJSONFile, getProcFNFromOrigFN

import multiprocessing as mp

# Will hold loaded projects
loadedProjects = []

# Initiate the donwsampling pool
downsamplePool = None

def downsampleFile(filepath: str, destinationpath: str) -> bool:
    """
    Downsamples an original file, placing the processed file in the destination folder.
    Raises an exception in case of error.
    :param filepath: path to the original file
    :param destinationpath: path to the destination folder
    :return: None
    """
    fp = Path(filepath)
    if not (fp.exists() and fp.is_file()):
        raise Exception(f"File '{filepath}' does not exist or is not a file.")

    dp = Path(destinationpath)
    if not (dp.exists() and dp.is_dir()):
        raise Exception(f"Destination '{destinationpath}' does not exist or is not a directory.")

    ds_file = File(None, -1, fp, dp / getProcFNFromOrigFN(fp))
    ds_file.process()
    ds_file.close()
    del ds_file

# Sets a global downsample
def instantiatePool(pool):
    global downsamplePool
    if downsamplePool is None: 
        downsamplePool = pool


def getProject(id) -> Optional[Project]:
    """
    Returns the project with matching ID.
    :return: the project instance belonging to the id, or None if not found
    """
    global loadedProjects
    for p in loadedProjects:
        if p.id == id:
            return p
    return None

def getProjects() -> Dict[int, Project]:
    """
    Returns loaded projects as a dict.
    :return: dict mapped from project ID to project instance of all loaded projects
    """
    global loadedProjects
    return {p.id: p for p in loadedProjects}

def getProjectsPayload(user_id) -> List[Dict]:
    """
    Returns a list of project information accessible to a given user.
    :return: list of objects containing project information
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

def listAvailableProjects() -> List[List[str]]:
    """
    Returns list of available projects (ID, name, path) from the database.
    These projects are not necessarily loaded in memory (that is done using
    loadProjects() or loadProject().
    :return:
    """
    return [[p.id, p.name, p.path] for p in models.Project.query.all()]

def listLoadedProjects() -> List[List[str]]:
    """
    Returns list of projects loaded in memory (ID, name, path).
    :return: list of lists
    """
    return [[p.id, p.name, p.path] for p in loadedProjects]

def listUsers() -> List[List[str]]:
    """
    Returns list of users (ID, email, first name, last name)
    :return: list of lists
    """
    return [[u.id, u.email, u.first_name, u.last_name] for u in models.User.query.all()]

def loadProject(id) -> Optional[Project]:
    """
    Load a project into memory. Returns the project instance if successful.
    :return: the project instance, or None
    """
    global loadedProjects

    logging.info(f"Loading project {id}")

    p = models.Project.query.filter_by(id=id).first()

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

    return getProject(id)

def loadProjects() -> Dict[int, Project]:
    """
    Load or reload projects into memory. If new projects are found on disk, they
    will be added to the database & loaded as well. Returns the same output as
    getProjects().
    :return: dict mapped from project ID to project of all loaded projects
    """

    global loadedProjects

    # Instantiate a global downsample pool
    pool = mp.Pool(processes=mp.cpu_count()//2)
    instantiatePool(pool)

    logging.info("Loading projects.")

    # Reset projects to empty list
    loadedProjects = []
    notProcessedFiles = []

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
            # Instantiate project, and add to the list to be returned
            # TODO(gus): We need to have project take absolute path and project name!
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

            # Instantiate project
            # TODO(gus): We need to have project take absolute path and project name!
            loadedProjects.append(Project(project))

    # Delete all files that may have been downsampled incorrectly and adds unprocessed files to be downsampled
    for project in loadedProjects:
        for projFile in project.files:
            tmp_file = Path(str(projFile.procFilePathObj)+'.tmp')
            if tmp_file.exists():
                try:
                    projFile.procFilePathObj.unlink(missing_ok=True)
                except Exception as e:
                    raise RuntimeError(f"Downsample file {str(projFile.procFilePathObj)} exists and could not be deleted. The viewer will quit now. It is recommended that the processed file be deleted manually. \n{e}\n{traceback.format_exc()}")
                else:
                    tmp_file.unlink()

                logging.info(f"Partial processed file {str(projFile.procFilePathObj)} has been removed.")
            
            # Add all non processed files for downsampling
            if not projFile.procFilePathObj.exists():
                notProcessedFiles.append((str(projFile.origFilePathObj.resolve()), str(projFile.procFilePathObj.parent.resolve())))

    for downsampParam in notProcessedFiles:
        downsamplePool.apply_async(downsampleFile, downsampParam)


    logging.info("Finished loading projects.")

    return getProjects()

def scaffoldProjectFolder(projDirPathObj):
    """Generate the baseline project folder contents as needed"""

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

def setDataPath(path, load_projects=False) -> None:
    """
    Loads a data path for use via Python (instead of as a web server). If the
    optional load_projects parameter is False, then projects must be loaded
    manually using loadProject() or loadProjects().
    """

    set_data_path(path)

    app = Flask(__name__)
    app.config.update({
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(config['dataPathObj'] / 'database' / 'db.sqlite')}"+'?check_same_thread=False',
    })

    models.init_flask_app(app)
    app.app_context().push()

    if load_projects:
        loadProjects()

def validateProjectFolder(projDirPathObj):
    """Raises an exception if the project folder is invalid"""

    logging.info(f"Validating project folder {projDirPathObj}.")

    # Validate top-level folders, excluding dot-files
    for p in [p for p in projDirPathObj.iterdir() if not p.name.startswith('.')]:

        # Project folder should only contain directories
        if not p.is_dir():
            raise Exception(f'Project folder contains invalid file: {p}')

        # Validate expected top-level folder names
        if p.name not in ['originals', 'processed', 'templates']:
            raise Exception(f'Project folder contains invalid folder: {p}')

    # Validate expected template files if they exist.
    tp = projDirPathObj / "templates"
    if tp.exists():
        for p in [p for p in tp.iterdir()]:
            if p.name not in ['project_template.json', 'interface_templates.json'] and not p.name.startswith('.'):
                raise Exception(f'Project templates folder contains invalid file: {p}')

    # TODO(gus): Validate that originals have processed?

    logging.info(f'Finished validating project folder {projDirPathObj}.')
