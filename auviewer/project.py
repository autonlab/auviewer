"""Class and related functionality for projects."""
import importlib
import numpy as np

import datetime as dt
from io import BytesIO
import logging
import math
import pandas as pd
import pickle
import traceback
import random
from collections import Counter

from pathlib import Path
from sqlalchemy import and_
from sqlalchemy.orm import contains_eager, joinedload
from typing import AnyStr, List, Dict, Optional, Union

from . import models
from .patternset import PatternSet
from .config import config
from .file import File
from .shared import annotationDataFrame, annotationOrPatternOutput, getProcFNFromOrigFN, patternDataFrame

class Project:
    """Represents an auviewer project."""

    def __init__(self, projectModel, processNewFiles=True):
        """The project name should also be the directory name in the projects directory."""
        
        # Set id & name
        self.id = projectModel.id
        self.name = projectModel.name

        print(f"Loading project ID {self.id} ({self.name})... ", end='')
        
        # Set relevant paths
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

        # Load pattern sets
        self.loadPatternSets()

        # Load project files
        self.loadProjectFiles(processNewFiles)

        print(f"Complete")

    def createPatternSet(self, name: str, description=None, showByDefault: bool = True) -> PatternSet:
        """
        Create and return a new pattern set.
        :return: a new PatternSet instance
        """

        # Create pattern set in the database
        patternSetModel = models.PatternSet(project_id=self.id, name=name, description=description, show_by_default=showByDefault)
        models.db.session.add(patternSetModel)
        models.db.session.commit()

        # Instantiate PatternSet and add to the project's pattern sets
        ps = PatternSet(self, patternSetModel)
        self.patternsets[ps.id] = ps

        # Return the pattern set
        return ps

    def detectPatterns(
            self, 
            type, 
            series, 
            thresholdlow, 
            thresholdhigh, 
            duration, 
            persistence, 
            maxgap, 
            expected_frequency=0, 
            min_density=0,
            drop_values_below=None,
            drop_values_above=None,
            drop_values_between=None,
        ):
        """
        Run pattern detection on all files, and return a DataFrame of results.
        This DataFrame, or a subset thereof, can be passed into PatternSet.addPatterns() if desired.
        """
        patterns = [[f.id, f.name, series, pattern[0], pattern[1], None, None] for f in self.files for pattern in f.detectPatterns(
            type, 
            series, 
            thresholdlow, 
            thresholdhigh, 
            duration, 
            persistence, 
            maxgap, 
            expected_frequency=expected_frequency, 
            min_density=min_density, 
            drop_values_below=drop_values_below, 
            drop_values_above=drop_values_above, 
            drop_values_between=drop_values_between
        )]
        pdf = pd.DataFrame(patterns, columns=['file_id', 'filename', 'series', 'left', 'right', 'top', 'bottom'])
        pdf['label'] = ''
        return pdf

    def getAnnotations(
            self,
            annotation_id: Union[int, List[int], None] = None,
            file_id: Union[int, List[int], None] = None,
            pattern_id: Union[int, List[int], None] = None,
            pattern_set_id: Union[int, List[int], None]=None,
            series: Union[AnyStr, List[AnyStr], None]=None,
            user_id: Union[int, List[int], None] = None) -> pd.DataFrame:
        """
        Returns a dataframe of annotations for this project, optionally filtered.
        """

        # Prepare input
        if not isinstance(annotation_id, List) and annotation_id is not None:
            annotation_id = [annotation_id]
        if not isinstance(file_id, List) and file_id is not None:
            file_id = [file_id]
        if not isinstance(pattern_id, List) and pattern_id is not None:
            pattern_id = [pattern_id]
        if not isinstance(pattern_set_id, List) and pattern_set_id is not None:
            pattern_set_id = [pattern_set_id]
        if not isinstance(series, List) and series is not None:
            series = [series]
        if not isinstance(user_id, List) and user_id is not None:
            user_id = [user_id]

        # Query
        q = models.Annotation.query.options(joinedload(models.Annotation.user))

        # Filter query as necessary
        if annotation_id is not None:
            q = q.filter(models.Annotation.id.in_(annotation_id))
        if file_id is not None:
            q = q.filter(models.Annotation.file_id.in_(file_id))
        if pattern_id is not None:
            q = q.filter(models.Annotation.pattern_id.in_(pattern_id))
        if pattern_set_id is not None:
            q = q.filter(models.Annotation.pattern_set_id.in_(pattern_set_id))
        if series is not None:
            q = q.filter(models.Annotation.series.in_(series))
        if user_id is not None:
            q = q.filter(models.Annotation.user_id.in_(user_id))

        # Return the dataframe
        return annotationDataFrame(q.filter(models.Annotation.project_id == self.id).all())

    def getAnnotationsOutput(self, user_id: int):
        """Returns a list of user's annotations for all files in the project"""
        return [[a.id, a.file_id, Path(a.file.path).name, a.series, a.left, a.right, a.top, a.bottom, a.label, a.pattern_id] for a in models.Annotation.query.filter_by(user_id=user_id, project_id=self.id).all()]

    def getFile(self, id):
        """Returns the file with matching ID or None."""
        for f in self.files:
            if f.id == id:
                return f
        return None

    def getFileByName(self, name):
        """Returns the file with matching ID or None."""
        for f in self.files:
            if f.name == name:
                return f
        return None

    def makeFilesPayload(self, files):
        # for f in files:
        #     f.initfile()
        outputObject = {
            'files': [[f.id, f.origFilePathObj.name] for f in files],
            'series': [],
            'events': [],#[f.getEvents() for f in self.files],
            'metadata': [f.getMetadata() for f in files]
        }

        #must populate outputObject with constituent files' series, events, and metadata
        for f in files:
            s = self.getSeriesToRender(f)
            if (s):
                outputObject['series'].append({s.id:  s.getFullOutput()})
            else:
                outputObject['series'].append({None: None})

        return outputObject

    def getConstituentFilesPayload(self):
        files = self.files

        return self.makeFilesPayload(files)

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
                    annotationOrPatternOutput(p, p.annotations[0] if len(p.annotations) > 0 else None) for p in models.db.session.query(models.Pattern).filter_by(pattern_set_id=ps.id).outerjoin(models.Annotation, and_(models.Annotation.pattern_id == models.Pattern.id, models.Annotation.user_id == user_id)).options(contains_eager(models.Pattern.annotations)).all()
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

    def getPatterns(
            self,
            file_id: Union[int, List[int], None] = None,
            pattern_id: Union[int, List[int], None] = None,
            pattern_set_id: Union[int, List[int], None] = None,
            series: Union[AnyStr, List[AnyStr], None] = None,
            user_id: Union[int, List[int], None] = None) -> pd.DataFrame:
        """Returns a dataframe of patterns for this project, optionally filtered."""

        # Prepare input
        if not isinstance(file_id, List) and file_id is not None:
            file_id = [file_id]
        if not isinstance(pattern_id, List) and pattern_id is not None:
            pattern_id = [pattern_id]
        if not isinstance(pattern_set_id, List) and pattern_set_id is not None:
            pattern_set_id = [pattern_set_id]
        if not isinstance(series, List) and series is not None:
            series = [series]
        if not isinstance(user_id, List) and user_id is not None:
            user_id = [user_id]

        # Query
        q = models.Pattern.query

        # Filter query as necessary
        if file_id is not None:
            q = q.filter(models.Pattern.file_id.in_(file_id))
        if pattern_id is not None:
            q = q.filter(models.Pattern.pattern_id.in_(pattern_id))
        if pattern_set_id is not None:
            q = q.filter(models.Pattern.pattern_set_id.in_(pattern_set_id))
        if series is not None:
            q = q.filter(models.Pattern.series.in_(series))
        if user_id is not None:
            q = q.filter(models.Pattern.user_id.in_(user_id))

        # Return the dataframe
        return patternDataFrame(q.filter(models.Pattern.project_id == self.id).all())


    def getPatternSet(self, id) -> Optional[PatternSet]:
        """
        Get project's pattern set by ID.
        :return: the PatternSet instance belonging to the id, or None if not found
        """
        return self.patternsets[id] if id in self.patternsets else None

    def getPatternSets(self) -> Dict[int, PatternSet]:
        """
        Get project's pattern sets.
        :return: a dict of the project's PatternSet instances, indexed by id
        """
        return self.patternsets.copy()

    def getTotalPatternCount(self) -> int:
        """
        Get total count of patterns in all the project's pattern sets
        :return: number of patterns
        """
        return sum([ps.count for ps in self.patternsets.values()])

    def listFiles(self) -> List[List[str]]:
        """
        Returns list of files for the project (ID, filename, file path, downsample path).
        :return: list of lists
        """
        return [[f.id, f.name, str(f.origFilePathObj), str(f.procFilePathObj)] for f in self.files]

    def listPatternSets(self) -> List[List[str]]:
        """
        Returns list of pattern sets (ID, names).
        :return: list of l:return:
        """
        return [[ps.id, ps.name] for ps in self.patternsets.values()]

    def loadPatternSets(self) -> None:
        """Load or reload the project's pattern sets."""

        # Reset pattern sets container
        self.patternsets = {}

        # Load pattern sets
        for psm in models.PatternSet.query.filter_by(project_id=self.id).all():
            self.patternsets[psm.id] = PatternSet(self, psm)

    def loadProjectFiles(self, processNewFiles=True):
        """Load or reload files belonging to the project, and process new files if desired."""

        # Reset files list
        self.files = []

        # Will hold all project files that exist in the database (in order to
        # detect new files to process).
        existingFilePathObjs = []

        # Get all of the project's files listed in the database
        fileDBModels = models.File.query.filter_by(project_id=self.id).all()

        # For each project file in the database...
        for fileDBModel in fileDBModels:

            # Verify the original file exists on the file system
            origFilePathObj = Path(fileDBModel.path)
            if origFilePathObj.exists():
                existingFilePathObjs.append(origFilePathObj)
            else:
                logging.error(f"File ID {fileDBModel.id} in the database is missing the original file on the file system at {fileDBModel.path}")
                continue
                # TODO(gus): Do something else with this? Like set error state in the database entry and display in GUI?

            # Verify the processed file exists on the file system
            procFilePathObj = self.processedDirPathObj / getProcFNFromOrigFN(origFilePathObj)
            if not procFilePathObj.exists():
                logging.error(f"File ID {fileDBModel.id} in the database is missing the processed file on the file system at {procFilePathObj}")
                #continue
                # TODO(gus): Do something else with this? Like set error state in the database entry and display in GUI?

            # Instantiate the file class, and attach to this project instance
            self.files.append(File(self, fileDBModel.id, origFilePathObj, procFilePathObj))

        # If processNewFiles is true, then go through and process new files
        if processNewFiles:

            # Get all existing absolute file paths as strings
            existingFilePathStrings = {str(p.resolve()): True for p in existingFilePathObjs}
                
            # For each new project file which does not exist in the database...
            for newOrigFilePathObj in self.originalsDirPathObj.iterdir():

                # Ensure that the path is absolute
                newOrigFilePathObj = newOrigFilePathObj.resolve()

                try:

                    # Check that the file exists (can happen in the case of a dead symlink)
                    if not newOrigFilePathObj.exists():
                        continue

                    # Skip if not file or not .h5
                    if not newOrigFilePathObj.is_file() or newOrigFilePathObj.suffix != '.h5':
                        continue

                    # Skip if matches any already-loaded files
                    if str(newOrigFilePathObj) in existingFilePathStrings:
                        continue

                    # Establish the path of the new processed file
                    newProcFilePathObj = self.processedDirPathObj / getProcFNFromOrigFN(newOrigFilePathObj)

                    # Now that the processing has completed (if not, an exception
                    # would have been raised), add the file to the database and
                    # update the file class instance ID.
                    newFileDBEntry = models.File(project_id=self.id, path=str(newOrigFilePathObj))
                    models.db.session.add(newFileDBEntry)
                    models.db.session.commit()

                    # Add a File class instance for this new file to the files list for this project
                    self.files.append(File(self, newFileDBEntry.id, newOrigFilePathObj, newProcFilePathObj))

                # Handle Ctrl-C
                except KeyboardInterrupt:
                    raise

                # Handle all other exceptions by logging and continuing
                except:
                    logging.error(f"Error loading new file: {traceback.format_exc()}")
        
        # Sort files by filename
        self.files.sort(key=lambda f: f.origFilePathObj.name)

    def setName(self, name):
        """Rename the project."""
        self.model.name = name
        models.db.session.commit()
        self.name = name
