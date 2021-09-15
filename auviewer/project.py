"""Class and related functionality for projects."""
import importlib
import numpy as np

import logging
import math
import pandas as pd
import traceback
import random
import datetime as dt

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

        # Load pattern sets
        self.loadPatternSets()

        # Load project files
        self.loadProjectFiles(processNewFiles)

    def __del__(self):
        """Cleanup"""
        try:
            self.observer.join()
        except:
            pass

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

    def detectPatterns(self, type, series, thresholdlow, thresholdhigh, duration, persistence, maxgap, expected_frequency=0, min_density=0):
        """
        Run pattern detection on all files, and return a DataFrame of results.
        This DataFrame, or a subset thereof, can be passed into PatternSet.addPatterns() if desired.
        """
        patterns = [[f.id, f.name, series, pattern[0], pattern[1], None, None] for f in self.files for pattern in f.detectPatterns(type, series, thresholdlow, thresholdhigh, duration, persistence, maxgap, expected_frequency=expected_frequency, min_density=min_density)]
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
        q = models.Annotation.query.options(joinedload('user'))

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
        outputObject = {
            'files': [[f.id, f.origFilePathObj.name] for f in files],
            'series': [],
            'events': [],#[f.getEvents() for f in self.files],
            'metadata': [f.getMetadata() for f in files]
        }

        #must populate outputObject with constituent files' series, events, and metadata
        for f in files:
            for s in f.series:
                outputObject['series'].append({s.id: s.getFullOutput()})
        
        return outputObject

    def getConstituentFilesPayload(self):
        files = self.files
        
        return self.makeFilesPayload(files)

    def queryWeakSupervision(self, queryObj, fileIds=None):
        #of form:
            # 'randomFiles': True,
            # 'categorical': None,
            # 'labelingFunction': None,
            # 'amount': 5
        chosenFiles = []
        if fileIds:
            fileDict = dict()
            for f in self.files:
                fileDict[f.id] = f
            for fId in fileIds:
                chosenFiles.append(fileDict[fId])
        elif queryObj['randomFiles']:
            chosenFileIds = set()
            while (len(chosenFiles) < min(len(self.files), queryObj.get('amount', 100))):
                nextFile = random.choice(self.files)
                while (nextFile.id in chosenFileIds):
                    nextFile = random.choice(self.files)
                chosenFiles.append(nextFile)
                chosenFileIds.add(nextFile.id)
        elif queryObj.get('labelingFunction'): #category belonging to labeling function
        #of form:
            # 'randomFiles': false,
            # 'categorical': 'ABSTAIN',
            # 'labelingFunction': 'bimodel_aEEG',
            # 'amount': 5,

            #extract labeler and category from tables
            print('getting query response')
            labeler = models.Labeler.query.filter_by(project_id=self.id, title=queryObj['labelingFunction']).first()
            category = models.Category.query.filter_by(project_id=self.id, label=queryObj['categorical']).first()
            categories = models.Category.query.filter_by(project_id=self.id, label=queryObj['categorical']).all()
            print([c.label for c in categories])
            print(labeler.title, category.label)
            print(len(self.files))
            # get votes belonging to labeling function, then votes belonging to category
            print([v for v in models.Vote.query.filter_by(category_id=category.id).all()])
            print([v for v in models.Vote.query.filter_by(labeler_id=labeler.id, category_id=category.id).all()])
            filteredVotes = models.Vote.query.filter_by(labeler_id=labeler.id).filter_by(category_id=category.id).all()
            print(filteredVotes)
            #basically doing a join w/o using a join here
            chosenFiles = [next(f for f in self.files if f.id==vote.file_id) for vote in filteredVotes]
        
        return self.makeFilesPayload(chosenFiles)

    def areSupervisorVotesWithTimeSegmentInDb(self, timeSegment):
        if (not timeSegment): return False
        #go through all files and check

        #spot check for single file
        checkFile = self.files[1]
        votesForFile = models.Vote.query.filter_by(project_id=self.id, file_id=checkFile.id).all()
        fileSeries = checkFile.series[0].getFullOutput().get('data') #for now assuming a single series, hence the 0-index
        smallestDiff = None
        print(len(votesForFile))
        for vote in votesForFile:
            left, right = dt.datetime.fromtimestamp(fileSeries[vote.leftIndex][0]), dt.datetime.fromtimestamp(fileSeries[vote.rightIndex-1][0])
            diff = right-left
            difference = abs(diff.total_seconds()*1000 - timeSegment) 
            if not smallestDiff:
                smallestDiff = difference
            else:
                smallestDiff = min(smallestDiff, difference)
            if difference <= 5000:
                #if a vote applies to a timesegment within 5 second of our timesegment length then we probably published these votes
                return True
        print(smallestDiff)
        return False

    def previewThresholds(self, fileIds, thresholds, labeler, timesegment):
        voteOutput = list()
        endIndicesOutput = list()
        for fileId in fileIds:
            votes, endIndices = self.computeVotes(fileId, labeler, timesegment, thresholds)
            voteOutput.append(votes)
            endIndicesOutput.append(endIndices)
        return voteOutput, endIndicesOutput


    def computeVotes(self, fileId, labelerTitle, timeSegment, modifiedThresholds=None):
        #find file corresponding to fileId
        for f in self.files:
            if f.id == fileId:
                series = f.series[0].getFullOutput().get('data') #for now assuming a single series, hence the 0-index

        lfModule = 'diagnoseEEG'
        labelingFunctionModuleSpec = importlib.util.spec_from_file_location(lfModule, f"EEG_Weak_Supervision_Code/{lfModule}.py")
        labelingFunctionModule = importlib.util.module_from_spec(labelingFunctionModuleSpec)
        labelingFunctionModuleSpec.loader.exec_module(labelingFunctionModule)
        lfModule = getattr(labelingFunctionModule, lfModule)

        thresholds = lfModule.getInitialThresholds()

        if (modifiedThresholds):
            for thresholdDict in modifiedThresholds:
                title, value = thresholdDict['title'], thresholdDict['value']
                print(type(value), value)
                thresholds[title] = float(value)
        labels = {
            'ABSTAIN': 'ABSTAIN',
            'NORMAL': 'NORMAL',
            'SUPPRESSED': 'SUPPRESSED',
            'SUPPRESSED_WITH_ICTAL': 'SUPPRESSED_WITH_ICTAL',
            'BURST_SUPRESSION': 'BURST_SUPRESSION',
        }

        timestamps = np.array([dt.datetime.fromtimestamp(e[0]) for e in series])

        bucketedSeries = list()
        bucketedVotes = list()
        endIndices = list()
        curStart, curEnd = 0, 0
        while (curEnd < len(timestamps)):
            curDiff = timestamps[curEnd] - timestamps[curStart]
            curBucket = []
            while (curDiff.total_seconds()*1000 < timeSegment):
                curBucket.append(series[curEnd][-1])
                curEnd += 1
                if (curEnd == len(timestamps)):
                    break
                curDiff = timestamps[curEnd] - timestamps[curStart]
            curStart = curEnd
            endIndices.append(curEnd)
            bucketedSeries.append(curBucket)
        startIdx = 0
        for i, curSeries in enumerate(bucketedSeries):
            filledNaNs = None # Indices where NaNs present 
            curSeries = np.array(curSeries)
            if np.sum(np.isnan(curSeries)) > 0:
                filledNaNs = curSeries.isna().to_numpy()
                curSeries = curSeries.fillna(0)

            if (np.sum(curSeries) == 0): continue
            EEG = curSeries.reshape((-1, 1))

            # apply lfs to series
            currentLfModule = lfModule(EEG, filledNaNs, thresholds, labels=labels, verbose =False, explain =False)

            labeler = getattr(currentLfModule, labelerTitle)
            # add label functions to labelers table
            votes = labeler()
            bucketedVotes.append(votes)
        return bucketedVotes, endIndices

    def getVotes(self):
        pass

    def getSegments(self):
        allSegments = models.Segment.query.filter_by(project_id=self.id).all()
        res = dict()
        for segment in allSegments:
            filename = self.getFile(segment.file_id).name
            series = segment.series
            bound = [segment.left, segment.right]
            res[filename] = res.get(filename, dict())
            print(res)
            res[filename][series] = res[filename].get(series, list())
            res[filename][series].append(bound)
        return res

    def createSegments(self, segmentsMap):
        beforeNum = len(models.Segment.query.filter_by(project_id=self.id).all())
        '''
        segmentsMap expected to be of form:
            { fId1: { seriesId1: [[left1, right1],
                                  [left2, right2]
                                 ],
                      seriesId2: [ ...,
                                   ...
                                 ]
                    },
              fId2: {...}
            }
        '''
        newSegments = []
        for filename, seriesMap in segmentsMap.items():
            for seriesId, spans in seriesMap.items():
                for span in spans:
                    left, right = span
                    newSegment = models.Segment(
                        project_id=self.id,
                        file_id=self.getFileByName(filename).id,
                        series=seriesId,
                        left=left,
                        right=right
                    )
                    newSegments.append(newSegment)
        models.db.session.add_all(newSegments)
        models.db.session.commit()

        afterNum = len(models.Segment.query.filter_by(project_id=self.id).all())
        success = (afterNum-beforeNum)==len(newSegments)
        print(beforeNum, afterNum, len(newSegments))
        print(f'It is {success} that we made as many segments as we intended')
        return segmentsMap, True, len(newSegments)
    
    def getLFCode(self, lfNames, lfModule, thresholds, labels):
        curSeries = self.files[0].series[0].getFullOutput().get('data') #for now assuming a single series, hence the 0-index
        curSeries = np.array([x[-1] for x in curSeries])
        filledNaNs = None
        if np.sum(np.isnan(curSeries)) > 0:
            filledNaNs = curSeries.isna().to_numpy()
            curSeries = curSeries.fillna(0)

        EEG = curSeries.reshape((-1, 1))

        # apply lfs to series
        currentLfModule = lfModule(EEG, filledNaNs, thresholds, labels=labels, verbose =False, explain =False)
        namesToCode = dict()
        import inspect
        for lfName in lfNames:
            try:
                lf = getattr(currentLfModule, lfName)
                namesToCode[lfName] = inspect.getsource(lf)
            except:
                continue
        return namesToCode

    def getLFStats(self, lfModule="diagnoseEEG", timeSegment=30*60*1000):
        _ = self.calculateAll(timeSegment, lfModule)
        labelingFunctionModuleSpec = importlib.util.spec_from_file_location(lfModule, f"EEG_Weak_Supervision_Code/{lfModule}.py")
        labelingFunctionModule = importlib.util.module_from_spec(labelingFunctionModuleSpec)
        labelingFunctionModuleSpec.loader.exec_module(labelingFunctionModule)
        lfModule = getattr(labelingFunctionModule, lfModule)
        lfs = lfModule.get_LF_names()
        res = dict()
        for lfName in lfs:
            statsDict = {
                'coverage': None,
                'overlaps': None,
                'conflicts': None
            }
            labeler = models.Labeler.query.filter_by(project_id=self.id,title=lfName).first()
            nonAbstains = len(list(filter(lambda v: v.category.label != 'ABSTAIN', labeler.votes)))
            print(nonAbstains, len(labeler.votes), lfName)
            statsDict['coverage'] = nonAbstains / len(labeler.votes)
            #overlaps
            #conflicts
            #coverage

            res[lfName] = statsDict
        return res
    
    def calculateAll(self, timeSegment, lfModule="diagnoseEEG"):
        self.applyLFsToDict([], {}, lfModule, timeSegment, constructAll=True)
        return

    def applyLFsToDict(self, fileIds, d, lfModule="diagnoseEEG", timeSegment=None, constructAll=False):
        labelingFunctionModuleSpec = importlib.util.spec_from_file_location(lfModule, f"EEG_Weak_Supervision_Code/{lfModule}.py")
        labelingFunctionModule = importlib.util.module_from_spec(labelingFunctionModuleSpec)
        labelingFunctionModuleSpec.loader.exec_module(labelingFunctionModule)
        lfModule = getattr(labelingFunctionModule, lfModule)

        # print('gonna drop_all then create_all')
        # models.db.drop_all()
        # models.db.create_all()
        # print('did it')
        # print(1/0)

        #### copied from 'EEG weak supervision.ipynb', Mononito's jupyter notebook
        thresholds = {
            'near_zero': 1,
            'near_zero_duration_tol': 5, # Duration of time that aEEG is near zero
            'EEG__HIGH_15': 15,
            'EEG__HIGH_10': 10,
            'EEG__HIGH_5': 5,
            'EEG__HIGH_4': 4,
            'EEG__LOW': 2, # 2
            'length_EEG__LOW': 25,
            'min_separation': 4,
            'n_high_amplitude_peaks_per_hour': 12,
            'min_fraction_high_amplitude': 0.1, 
            'splits': 6, # Number of non-overlappying moving windows (1 hour durations)
        }

        labels = {
            'ABSTAIN': 'ABSTAIN',
            'NORMAL': 'NORMAL',
            'SUPPRESSED': 'SUPPRESSED',
            'SUPPRESSED_WITH_ICTAL': 'SUPPRESSED_WITH_ICTAL',
            'BURST_SUPRESSION': 'BURST_SUPRESSION',
        }
        #### end of copied vars

        voteOutputs = []
        labelerNamesToIds = dict()
        uniqueCategories = set()
        categoryNamesToIds = dict()
        if (constructAll):
            shouldConstructLabelers = True
            shouldConstructThresholds = True
            shouldConstructCategories = True
            shouldQueryForVotes = False
        else:

            numLabelersInDb = len(models.Labeler.query.filter_by(project_id=self.id).all())
            shouldConstructLabelers = numLabelersInDb == 0

            shouldConstructThresholds = len(models.Threshold.query.filter_by(project_id=self.id).all()) == 0

            shouldConstructCategories = len(models.Category.query.filter_by(project_id=self.id).all()) == 0

            shouldQueryForVotes = self.areSupervisorVotesWithTimeSegmentInDb(timeSegment)#(shouldConstructLabelers or (not shouldConstructLabelers and numVotesInDb != len(self.files)*numLabelersInDb)
        print(shouldConstructLabelers, shouldConstructCategories, not shouldQueryForVotes)

        fileSeries = dict()
        for f in self.files:
            if (not shouldQueryForVotes): #then add every file to fileSeries
                fileSeries[f.id] = f.series[0].getFullOutput().get('data') #for now assuming a single series, hence the 0-index
            elif f.id in fileIds:
                fileSeries[f.id] = f.series[0].getFullOutput().get('data') #for now assuming a single series, hence the 0-index

        if (shouldConstructCategories):
            print(f'Constructing the following categories: {labels.keys()}')
            # add categories to table
            newCategories = list()
            for label in labels.keys():
                newCategory = models.Category(
                    project_id=self.id,
                    label=label)
                newCategories.append(newCategory)
            print(f'Before: {models.Category.query.filter_by(project_id=self.id).all()}')
            models.db.session.add_all(newCategories)
            models.db.session.commit()
            print(f'After: {models.Category.query.filter_by(project_id=self.id).all()}')

        lfNames = lfModule.get_LF_names()
        newLabelers = []
        if (shouldConstructLabelers):
            print('Constructing labelers')
            for lfName in lfNames:
                newLabeler = models.Labeler(
                    project_id=self.id,
                    title=lfName)
                newLabelers.append(newLabeler)
            models.db.session.add_all(newLabelers)
            models.db.session.commit()
            print(f'After labeler construction: {models.Labeler.query.filter_by(project_id=self.id).all()}')
        

        #construct labelerNamesToIds and categoryNamesToIds, for vote creation
        for lfName in lfNames:
            labeler = models.Labeler.query.filter_by(project_id=self.id, title=lfName).first()
            labelerNamesToIds[lfName] = labeler.id #once committed, each labeler has an id

        for categoryLabel in labels.keys():
            curCategory = models.Category.query.filter_by(project_id=self.id, label=categoryLabel).first()
            categoryNamesToIds[categoryLabel] = curCategory.id

        if (shouldConstructThresholds):
            print('Constructing thresholds and associations')
            labelersToThresholds = lfModule.getThresholdsForLabelers()
            thresholdVals = lfModule.getInitialThresholds()
            newThresholds = list()
            for threshold, value in thresholdVals.items():
                newThreshold = models.Threshold(
                    project_id = self.id,
                    title = threshold,
                    value = value
                )
                newThresholds.append(newThreshold)
            models.db.session.add_all(newThresholds)
            models.db.session.commit()
            print(f'Added {len(newThresholds)} new thresholds')

            thresholdToObj = dict(zip(thresholdVals.keys(), newThresholds))
            for labeler in newLabelers:
                for threshold in labelersToThresholds[labeler.title]:
                    labeler.thresholds.append(thresholdToObj[threshold])
                    models.db.session.commit()

        voteOutputs = list() # len(fileSeries) x math.ceil(time_duration_ms / time_segment) x num_labelers
        endIndicesForFile = list()
        for fId, series in fileSeries.items():
            print(fId)
            if (timeSegment != None):
                timestamps = np.array([dt.datetime.fromtimestamp(e[0]) for e in series])
                bucketedVotes = list() 
                endIndices = list()
                if (not shouldQueryForVotes):
                    # print(series[0][0], series[1][0], series[-1][0])
                    # print(timestamps[0], timestamps[1], timestamps[-1])
                    bucketedSeries = list()
                    curStart, curEnd = 0, 0
                    while (curEnd < len(timestamps)):
                        curDiff = timestamps[curEnd] - timestamps[curStart]
                        curBucket = []
                        while (curDiff.total_seconds()*1000 < timeSegment):
                            curBucket.append(series[curEnd][-1])
                            curEnd += 1
                            if (curEnd == len(timestamps)):
                                break
                            curDiff = timestamps[curEnd] - timestamps[curStart]
                        curStart = curEnd
                        endIndices.append(curEnd)
                        bucketedSeries.append(curBucket)
                    startIdx = 0
                    for i, curSeries in enumerate(bucketedSeries):
                        filledNaNs = None # Indices where NaNs present 
                        curSeries = np.array(curSeries)
                        if np.sum(np.isnan(curSeries)) > 0:
                            filledNaNs = curSeries.isna().to_numpy()
                            curSeries = curSeries.fillna(0)

                        if (np.sum(curSeries) == 0): continue
                        EEG = curSeries.reshape((-1, 1))

                        # apply lfs to series
                        try:
                            currentLfModule = lfModule(EEG, filledNaNs, thresholds, labels=labels, verbose =False, explain =False)
                        except:
                            break

                        # add label functions to labelers table
                        votes = currentLfModule.get_vote_vector()
                        if (shouldConstructCategories): uniqueCategories.update(votes)
                        bucketedVotes.append(votes)

                        endIdx = endIndices[i]
                        # print(startIdx, endIdx)
                        # left, right = series[startIdx][0], series[endIdx-1][0]
                        #add votes to db
                        # print(f'Before vote creation for fId {fId}: {len(models.Vote.query.filter_by(project_id=self.id, file_id=fId).all())}')
                        createdVotes = list()
                        for vote, labeler in zip(votes, lfNames):
                            categoryId = categoryNamesToIds[vote]
                            labelerId = labelerNamesToIds[labeler]
                            newVote = models.Vote(
                                project_id=self.id,
                                labeler_id=labelerId,
                                category_id=categoryId,
                                file_id=fId,
                                leftIndex=startIdx,
                                rightIndex=endIdx)
                            createdVotes.append(newVote)
                        models.db.session.add_all(createdVotes)
                        models.db.session.commit()
                        # print(f'After: {len(models.Vote.query.filter_by(project_id=self.id, file_id=fId).all())}')

                        startIdx = endIdx
                else:
                    # print('Querying instead:')
                    firstRunThrough = True
                    def isOfTimeSegmentLength(leftIdx, rightIdx):
                        left, right = timestamps[leftIdx], timestamps[rightIdx-1]
                        diff = right - left
                        timeDiffInMs = abs(diff.total_seconds()*1000 - timeSegment)


                        if timeDiffInMs < 3000:
                            if firstRunThrough:
                                endIndices.append(rightIdx)
                            return True
                        else:
                            #left over case is true when 
                            totalSeriesDuration = (timestamps[-1] - timestamps[0]).total_seconds() * 1000
                            leftOverSegmentLength = totalSeriesDuration % timeSegment
                            d = abs(leftOverSegmentLength - diff.total_seconds()*1000)
                            # print(d)
                            # print(1/0)
                            if (d <= 3000):
                                if firstRunThrough:
                                    endIndices.append(rightIdx)
                                return True
                            return False
                    # get votes from DB
                    allVotes = list()
                    for lfName in lfNames:
                        labeler = models.Labeler.query.filter_by(id=labelerNamesToIds[lfName]).first()
                        votesForProjAndFile = list(filter(lambda v: v.project_id == self.id and v.file_id == fId, labeler.votes)) #ordered by startIndex already
                        votes = list(map(lambda v: v.category.label, filter(lambda v: isOfTimeSegmentLength(v.leftIndex, v.rightIndex), votesForProjAndFile)))
                        # print(f'\tCulled from {len(votesForProjAndFile)} votes to {len(votes)}')
                        # print(f'\tvotes: {votes}')
                        firstRunThrough = False
                        allVotes.append(votes)
                        # print(f'got {len(votes)} votes')
                    bucketedVotes = zip(*allVotes) #reshape allVotes from lfs x timesegments to timesegments x lfs

                    # allVotes = models.Vote.query.filter_by(project_id=self.id, file_id=fId).all()
                    # votes = list(filter(lambda v: isOfTimeSegmentLength(v.leftIndex, v.rightIndex), allVotes))
                    # if (len(votes) != math.ceil(totalSeriesDuration.total_seconds()*1000 / timeSegment)):
                    #     #need to find left over vote
                    #     maxRightIndex = votes[0].rightIndex
                    #     for vote in votes:
                    #         maxRightIndex = max(vote.rightIndex, maxRightIndex)
                    #     leftOverVotes = list()
                    #     for vote in allVotes:
                    #         if vote.leftIndex == maxRightIndex:
                    #             leftOverVotes.append(vote)

                endIndicesForFile.append(endIndices)
                voteOutputs.append(list(bucketedVotes))


                # print(len(bucketedSeries), len(bucketedSeries[0]), len(bucketedSeries[-1]))
                # diff = timestamps[-1] - timestamps[0]
                # print(diff.total_seconds() * 1000)
                # print((diff.total_seconds() * 1000) // timeSegment)

            # if (not shouldConstructVotes):
            #     # get votes from db
            #     models.Vote.query()
            # else:

            # filledNaNs = None # Indices where NaNs present 
            # series = np.array([e[-1] for e in series])
            # if np.sum(np.isnan(series)) > 0:
            #     filledNaNs = series.isna().to_numpy()
            #     series = series.fillna(0)

            # if (np.sum(series) == 0): continue
            # EEG = series.reshape((-1, 1))

            # # apply lfs to series
            # currentLfModule = lfModule(EEG, filledNaNs, thresholds, labels=labels, verbose =False, explain =False)

            # votes = currentLfModule.get_vote_vector()
            # if (shouldConstructCategories): uniqueCategories.update(votes)
            # voteOutputs.append(votes)
        


        
        # if (shouldConstructVotes):
        #     createdVotes = list()
        #     print(f'Before vote creation: {models.Vote.query.filter_by(project_id=self.id).all()}')
        #     for votes, fileId in zip(voteOutputs, fileSeries.keys()):
        #         for vote, labeler in zip(votes, lfNames):
        #             categoryId = categoryNamesToIds[vote]
        #             labelerId = labelerNamesToIds[labeler]
        #             newVote = models.Vote(
        #                 project_id=self.id,
        #                 labeler_id=labelerId,
        #                 category_id=categoryId,
        #                 file_id=fileId)
        #             createdVotes.append(newVote)
        #     models.db.session.add_all(createdVotes)
        #     models.db.session.commit()
        #     print(f'After: {models.Vote.query.filter_by(project_id=self.id).all()}')

        #     #since we added everything to fileSeries so we created all votes, we should now filter out files not present in fileIds
        #     votesByFileId = list(zip(fileSeries.keys(), voteOutputs))
        #     votesToKeep = list(map(lambda t: t[1], filter(lambda t: t[0] in fileIds, votesByFileId)))
        #     voteOutputs = votesToKeep
        #     print(f'Trimmed vote output from {len(votesByFileId)} to {len(voteOutputs)}')


        d['labeling_function_votes'] = voteOutputs
        d['labeling_function_titles'] = lfNames
        d['labeling_function_possible_votes'] = list(labels.keys())
        d['labelers_to_thresholds'] = lfModule.getThresholdsForLabelers()
        namesToCode = self.getLFCode(lfNames, lfModule, thresholds, labels)
        d['labeler_code'] = namesToCode 

        
        if (len(endIndicesForFile) > 0):
            d['time_segment_end_indices'] = endIndicesForFile
        return voteOutputs, lfNames, list(labels.keys())
    
    def getThresholdsPayload(self):
        thresholds = models.Threshold.query.filter_by(project_id=self.id).all()
        thresholds = dict(map(lambda x: (x.title, x.value), thresholds))
        return thresholds

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
            existingFilePathObjs.append(origFilePathObj)
            if not origFilePathObj.exists():
                logging.error(
                    f"File ID {fileDBModel.id} in the database is missing the original file on the file system at {fileDBModel.path}")
                continue
                # TODO(gus): Do something else with this? Like set error state in the database entry and display in GUI?

            # Verify the processed file exists on the file system
            procFilePathObj = self.processedDirPathObj / getProcFNFromOrigFN(origFilePathObj)
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
            for newOrigFilePathObj in self.originalsDirPathObj.iterdir():

                try:

                    # Skip if not file or not .h5
                    if not newOrigFilePathObj.is_file() or newOrigFilePathObj.suffix != '.h5':
                        continue

                    # Skip if matches any already-loaded files
                    if any(map(lambda existingFilePathObj: newOrigFilePathObj.samefile(existingFilePathObj), existingFilePathObjs)):
                        continue

                    # Establish the path of the new processed file
                    newProcFilePathObj = self.processedDirPathObj / getProcFNFromOrigFN(newOrigFilePathObj)

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

                except:

                    logging.error(f"Error loading new file: {traceback.format_exc()}")

    def setName(self, name):
        """Rename the project."""
        self.model.name = name
        models.db.session.commit()
        self.name = name
