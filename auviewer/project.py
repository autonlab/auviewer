"""Class and related functionality for projects."""
import importlib
import numpy as np

import datetime as dt
from io import StringIO, BytesIO
import logging
import math
import pandas as pd
import traceback
import random
# from snorkel.labeling import LFAnalysis
# from snorkel.labeling.model import LabelModel
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

    def queryWeakSupervision(self, queryObj, fileIds=None):
        newsm = None
        if (self.name.lower().startswith('afib') and len(models.SupervisorModule.query.filter_by(project_id=self.id).all()) == 0):
            newsm = models.SupervisorModule(
                project_id=self.id,
                title='diagnoseAFib',
                series_of_interest="/data/numerics/HR.BeatToBeat:value",
                series_to_render="/data/numerics/HR.BeatToBeat:value"
            )
        elif (self.name.lower().startswith('mitbih') and len(models.SupervisorModule.query.filter_by(project_id=self.id).all()) == 0):
            newsm = models.SupervisorModule(
                project_id=self.id,
                title='diagnoseAFib',
                series_of_interest="/data",
                series_to_render="/data"
            )
        print(models.SupervisorModule.query.filter_by(project_id=self.id).first().title)
        if (newsm):
            models.db.session.add(newsm)
            models.db.session.commit()
            print('made '+newsm.title + ' for proj '+self.name)

        #of form:
            # 'randomFiles': True,
            # 'categorical': None,
            # 'labelingFunction': None,
            # 'amount': 5
        chosenFiles = []
        if fileIds:
            fileDict = dict()
            for f in self.files:
                try:
                    f.f
                except Exception as e:
                    print(e)
                    pass
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
            labeler = models.Labeler.query.filter_by(project_id=self.id, title=queryObj['labelingFunction']).first()
            category = models.Category.query.filter_by(project_id=self.id, label=queryObj['categorical']).first()
            categories = models.Category.query.filter_by(project_id=self.id, label=queryObj['categorical']).all()
            # get votes belonging to labeling function, then votes belonging to category
            filteredVotes = models.Vote.query.filter_by(labeler_id=labeler.id).filter_by(category_id=category.id).all()
            #basically doing a join w/o using a join here
            chosenFiles = [next(f for f in self.files if f.id==vote.file_id) for vote in filteredVotes]

        return self.makeFilesPayload(chosenFiles)

    def previewThresholds(self, fileIds, thresholds, labeler, timesegment):
        voteOutput = list()
        endIndicesOutput = list()
        for fileId in fileIds:
            votes, endIndices = self.computeVotesForFile(fileId, labeler, thresholds)
            voteOutput.append(votes)
            endIndicesOutput.append(endIndices)
        return voteOutput, endIndicesOutput


    def computeVotesForFile(self, fileId, labelerTitle, modifiedThresholds=None):
        #find file corresponding to fileId
        for f in self.files:
            if f.id == fileId:
                series = self.getSeriesOfInterest(f).getFullOutput().get('data')

        lfModule = self.getLFModule()

        thresholds = lfModule.getInitialThresholds()

        if (modifiedThresholds):
            for thresholdDict in modifiedThresholds:
                title, value = thresholdDict['title'], thresholdDict['value']
                thresholds[title] = float(value)

        return []

    def getIndicesForSegments(self, segments, series):
        correspondingIndices = [None for i in range(len(segments))]
        # timestamps = np.array([dt.datetime.fromtimestamp(e[0]) for e in series])
        timestamps = np.array([e[0]*1000 for e in series])
        for i, t in enumerate(timestamps):
            if i==0: continue
            for j, seg in enumerate(segments):
                if correspondingIndices[j] != None:
                    # then we are looking for end index
                    if timestamps[i-1] <= seg.right and timestamps[i] >= seg.right:
                        correspondingIndices[j][1] = i
                    elif (i == len(timestamps) - 1):
                        # case where given segment spans out of bounds, so clamp
                        correspondingIndices[j][1] = i
                else:
                    # then we are looking for start index
                    if timestamps[i-1] <= seg.left and timestamps[i] >= seg.left:
                        correspondingIndices[j] = [i-1, None]
        return correspondingIndices

    def getLabels(self):
        lfMod = self.getLFModule()
        labels = lfMod.getLabels()
        return labels

    def getLabelers(self):
        lfMod = self.getLFModule()
        lfNames = lfMod.get_LF_names()
        return lfNames + ['LabelModel']

    def applyLabelModel(self, segIdxToDFIdx=None, dfdict=None, votes=None):
        lfMod = self.getLFModule()
        labels = lfMod.getLabels()
        lfNames = lfMod.get_LF_names()
        if (votes):
            pass
        elif (len(models.Vote.query.filter_by(project_id=self.id).all()) > 0):
            #use calculated votes
            votes, _ = self.getVotes([f.id for f in self.files])
        else:
            votes = self.computeVotes([f.id for f in self.files])
        segIds = sorted(votes.keys())
        L_train = []
        for segId in segIds:
            if (len(votes[segId]) > 0):
                L_train.append([labels[v] for v in votes[segId]])
        lfNumCorrect, lfNumNonAbstains = [0 for v in lfNames], [0 for v in lfNames]
        lfNumAbstains = [0 for v in lfNames]
        L_train = np.array(L_train)
        lm = LabelModel(cardinality=len(labels.keys()), verbose=False)
        lm.fit(L_train=L_train, n_epochs=500, log_freq=100, seed=42)
        lm_predictions = lm.predict_proba(L=L_train)
        predsByFilename = dict()
        numbersToLabels = lfMod.number_to_label_map()
        j= 0
        for i, segId in enumerate(segIds):
            if (len(votes[segId]) > 0):
                prediction = lm_predictions[j]
                p = np.argmax(prediction)
                #for experimental accuracy predictions
                for k, v in enumerate(votes[segId]):
                    if j == 0:
                        print(v, labels[v])
                    v = labels[v]
                    if v >= 0:
                        lfNumNonAbstains[k] += 1
                        if v == p:
                            lfNumCorrect[k] += 1
                    else:
                        lfNumAbstains[k] += 1
                segment = models.Segment.query.get(segId)
                filename = self.getFile(segment.file_id).name
                listToAppendTo = predsByFilename.get(filename, [])
                p = numbersToLabels[p-1]
                fin = int(self.getFile(segment.file_id).name.split(".")[0].split("_")[-1])
                # if (fin in searchFINs):
                #     dfdict['LabelModelVote'][segIdxToDFIdx[segId]] = p
                listToAppendTo.append({
                    'prediction': p,
                    'confidences': prediction.tolist(),
                    'left': segment.left,
                    'right': segment.right
                })
                predsByFilename[filename] = listToAppendTo
                j += 1

        # print('starting')
        # j = 0
        # lm_ml_labelsD = {
        #     'FIN_Study_ID': list(),
        #     'confidence': list(),
        #     'label': list(),
        #     'start': list(),
        #     'stop': list()
        # }

        # for segId in segIds:
        #     if (len(votes[segId]) > 0):
        #         prediction = lm_predictions[j]
        #         p = np.argmax(prediction)
        #         lm_label = numbersToLabels[p]
        #         segment = models.Segment.query.get(segId)
        #         fin = int(self.getFile(segment.file_id).name.split(".")[0].split("_")[-1])

        #         lm_ml_labelsD['FIN_Study_ID'].append(fin)
        #         lm_ml_labelsD['label'].append(lm_label)
        #         lm_ml_labelsD['confidence'].append(prediction[p])
        #         lm_ml_labelsD['start'].append(dt.datetime.fromtimestamp(segment.left/1000))
        #         lm_ml_labelsD['stop'].append(dt.datetime.fromtimestamp(segment.right/1000))

        #         j+=1
        # lm_ml_labels = pd.DataFrame(lm_ml_labelsD)
        # lm_ml_labels.to_csv('~/Documents/auton/localWorkspace/afib_detection/assets/gold/labelmodel_mladi_labels.csv')
        # print(lm_ml_labels.head())

        # predictions = list()
        # for prediction in lm_predictions:
        #     predictions.append(numbersToLabels[np.argmax(prediction)])
        analysis = LFAnalysis(L=L_train).lf_summary()
        analysis['experimental_accuracy'] = [lfNumCorrect[i]/lfNumNonAbstains[i] for i in range(len(lfNames))]
        return {
            # 'predictions': predictions,
            # 'probabilities': lm_predictions.tolist(),
            'lfs': lfNames,
            'lfInfo': analysis.to_json(),
            'predictions': predsByFilename
        }


    def deleteVotes(self):
        allVotes = models.Vote.query.filter_by(project_id=self.id).all()
        for vote in allVotes:
            models.db.session.delete(vote)
        models.db.session.commit()

    def getVotes(self, fileIds, windowInfo=None):
        result = dict()
        # searchFINs =[1215499, 1007711, 1998627]
        # searchFINs = []
        dfDict = {
            'FIN_Study_Id': list(),
            'segmentStart': list(),
            'segmentEnd': list(),
            'LabelModelVote': list()

        }
        lfModule = self.getLFModule()
        lfnames = lfModule.get_LF_names()
        thresholds = lfModule.getInitialThresholds()
        labels = lfModule.getLabels()
        m = lfModule.number_to_label_map()
        segIdxToDFIdx = dict()
        for lfname in lfnames:
            dfDict[lfname] = list()
            k = lfname.split('_')[0]
            dfDict[k] = list()
        j = 0
        for fileId in fileIds:
            f = self.getFile(fileId)
            fin = int(f.name.split('.')[0].split('_')[-1])

            if (windowInfo):
                segmentsForFile = models.Segment.query.\
                    filter_by(
                        project_id=self.id,
                        file_id=fileId,
                        type='WINDOW',
                        window_size_ms=windowInfo['window_size_ms'],
                        window_roll_ms=windowInfo['window_roll_ms']).\
                    order_by(
                        models.Segment.left.asc() #ascending
                ).all()
            else:
                segmentsForFile = models.Segment.query.filter_by(
                    project_id=self.id,
                    file_id=fileId,
                    type='CUSTOM'
                ).all()
            if fin in [None]:
                for segment in segmentsForFile:
                    series = self.getSeriesOfInterest(f).getRangedOutput(segment.left / 1000.0, segment.right / 1000.0).get('data')
                    if (len(series) == 0):
                        continue
                    curSeries = np.array([x[-1] for x in series])

                    filledNaNs = None
                    if np.sum(np.isnan(curSeries)) > 0:
                        filledNaNs = curSeries.isna().to_numpy()
                        curSeries = curSeries.fillna(0)
                    lfModule = self.getLFModule()
                    EEG = curSeries.reshape((-1, 1))
                    curLFModule = lfModule(EEG, filledNaNs, thresholds, labels)
                    vote_vec = curLFModule.get_vote_vector()
                    votes = zip(lfnames, [m[v] for v in vote_vec])
                    num_vec = curLFModule.get_numbers_vector()
                    nums = zip(lfnames, num_vec)
                    segStart = dt.datetime.fromtimestamp((segment.left) / 1000.0)
                    segEnd = dt.datetime.fromtimestamp((segment.right) / 1000.0)
                    segIdxToDFIdx[segment.id] = j
                    j += 1
                    dfDict['FIN_Study_Id'].append(fin)
                    dfDict['segmentStart'].append(segStart)
                    dfDict['segmentEnd'].append(segEnd)
                    dfDict['LabelModelVote'].append(None)
                    for name, vote in votes:
                        dfDict[name].append(vote)
                    for name, num in nums:
                        k = name.split('_')[0]
                        dfDict[k].append(num)
            for segment in segmentsForFile:
                votes = [v.category.label for v in segment.votes]
                result[segment.id] = votes
        #add labelmodel results
        preds = self.applyLabelModel(segIdxToDFIdx=segIdxToDFIdx, dfdict=dfDict, votes=result)
        # preds = None
        # df = pd.DataFrame.from_dict(dfDict)
        # df.to_csv('segmentsOfInterest.csv')
        return result, preds

    def computeVotes(self, fileIds, windowInfo=None):
        lfModule = self.getLFModule()
        thresholds = self.getThresholdsPayload()

        labels = lfModule.getLabels()
        resultingVotes = dict()
        self.deleteVotes()

        lfs = list(map(lambda x: models.Labeler.query.filter_by(project_id=self.id, title=x).first(), lfModule.get_LF_names()))
        categoryNumbersToIds = dict()
        m = lfModule.number_to_label_map()
        for number in labels.values():
            label = models.Category.query.filter_by(project_id=self.id, label=m[number]).first()
            categoryNumbersToIds[number] = label.id
        newVotes = list()
        for fileId in fileIds:
            f = self.getFile(fileId)
            if (self.getSeriesOfInterest(f) == None):
                continue


            if (windowInfo):
                segmentsForFile = models.Segment.query.\
                    filter_by(
                        project_id=self.id,
                        file_id=fileId,
                        type='WINDOW',
                        window_size_ms=windowInfo['window_size_ms'],
                        window_roll_ms=windowInfo['window_roll_ms']).\
                    order_by(
                        models.Segment.left.asc() #ascending
                ).all()
            else:
                segmentsForFile = models.Segment.query.filter_by(
                    project_id=self.id,
                    file_id=fileId,
                    type='CUSTOM'
                ).all()
            # mini = float('inf')
            # maxi = float('-inf')
            # for segment in segmentsForFile:
            #     mini = min(segment.left, mini)
            #     maxi = max(segment.right, maxi)
            # series = self.getSeriesOfInterest(f).getFullOutput().get('data')
            #iterate through user defined segments
            if (len(segmentsForFile) == 0): continue
            # correspondingIndexBounds = self.getIndicesForSegments(segmentsForFile, series)
            for i, segment in enumerate(segmentsForFile):
                # if (correspondingIndexBounds[i]):
                #     startIdx, endIdx = correspondingIndexBounds[i]
                # else:
                #     continue
                series = self.getSeriesOfInterest(f).getRangedOutput(segment.left / 1000.0, segment.right / 1000.0).get('data')
                if (len(series) == 0):
                    continue
                curSeries = np.array([x[-1] for x in series])

                filledNaNs = None
                if np.sum(np.isnan(curSeries)) > 0:
                    filledNaNs = curSeries.isna().to_numpy()
                    curSeries = curSeries.fillna(0)
                EEG = curSeries.reshape((-1, 1))
                curLFModule = lfModule(EEG, filledNaNs, thresholds, labels)
                vote_vec = curLFModule.get_vote_vector()
                resultingVotes[segment.id] = vote_vec
                for lf, vote in zip(lfs, vote_vec):
                    categoryId = categoryNumbersToIds[vote]
                    newVote = models.Vote(
                        project_id=self.id,
                        labeler_id=lf.id,
                        category_id=categoryId,
                        file_id=fileId,
                        segment_id=segment.id
                    )
                    newVotes.append(newVote)
                    # models.db.session.add(newVote)
                    # models.db.session.commit()

        numBefore = len(models.Vote.query.filter_by(project_id=self.id).all())
        models.db.session.add_all(newVotes)
        models.db.session.commit()
        numAfter = len(models.Vote.query.filter_by(project_id=self.id).all())
        print(f"Added {numAfter - numBefore} votes")
        return resultingVotes

    def getSegments(self, type='CUSTOM'):
        allSegments = models.Segment.query.filter_by(project_id=self.id, type=type).all()
        res = dict()
        for segment in allSegments:
            filename = self.getFile(segment.file_id).name
            series = segment.series
            bound = {'left': segment.left, 'right':segment.right, 'id': segment.id}
            res[filename] = res.get(filename, dict())
            res[filename][series] = res[filename].get(series, list())
            res[filename][series].append(bound)

        if type=='CUSTOM':
            windowInfo = None
        else:
            sampleSeg = models.Segment.query.filter_by(project_id=self.id, type='WINDOW').first()
            windowInfo = {
                'window_size_ms': sampleSeg.window_size_ms,
                'window_roll_ms': sampleSeg.window_roll_ms
            }
        return res, windowInfo

    def deleteSegments(self, segmentsMap):
        beforeNum = len(models.Segment.query.filter_by(project_id=self.id).all())
        segmentsToDelete = list()
        for filename, seriesMap in segmentsMap.items():
            for seriesId, spans in seriesMap.items():
                for span in spans:
                    left, right = span['left'], span['right']
                    segment = models.Segment.query.filter_by(project_id=self.id, file_id=self.getFileByName(filename).id, series=seriesId, left=left, right=right).first()
                    models.db.session.delete(segment)
                    segmentsToDelete.append(segment)
        models.db.session.commit()
        afterNum = len(models.Segment.query.filter_by(project_id=self.id).all())
        numDeleted = beforeNum - afterNum
        success = len(segmentsToDelete) == numDeleted
        return numDeleted, success

    def findFileByFIN(self, fin_id):
        for file in self.files:
            fin = file.name.split(".")[0].split("_")[-1]
            if fin == str(fin_id):
                return file
        return None

    def parseAndCreateSegmentsFromFile(self, filename, fileObj):
        fileContents = fileObj.read()
        if (filename.endswith('.pkl')):
            #assume its a pickled pandas dataframe
            df = pd.read_pickle(fileContents)
        elif (filename.endswith('.csv')):
            df = pd.read_csv(BytesIO(fileContents), parse_dates=['start', 'end'])
        self._deleteCustomSegments()
        foundFINs = dict() #dictionary mapping fins to their file indexes
        segmentsMap = dict()
        '''
        segmentsMap expected to be of form:
            { fId1: { seriesId1: [{'left': left1, 'right': right1},
                                  {'left': left2, 'right': right2}
                                 ],
                      seriesId2: [ ...,
                                   ...
                                 ]
                    },
              fId2: {...}
            }
        '''
        count = 0
        for idx, row in df.iterrows():
            fin_id = row['fin_id']
            foundFINs[fin_id] = foundFINs.get(fin_id, self.findFileByFIN(fin_id))
            if (not foundFINs[fin_id]):
                #then file in csv isn't associated with file, so we should skip making segments for it
                continue
            file = foundFINs[fin_id]
            series = self.getSeriesOfInterest(file)
            if (series is None):
                continue
            left_ms, right_ms = dt.datetime.timestamp(row['start'])*1000, dt.datetime.timestamp(row['end'])*1000
            newSeg = models.Segment(
                project_id=self.id,
                file_id=file.id,
                series=series.id,
                left=left_ms,
                right=right_ms,
                type='CUSTOM'
            )
            models.db.session.add(newSeg)

            if (not segmentsMap.get(file.name)):
                segmentsMap[file.name] = {series.id: list()}
            segmentsMap[file.name][series.id].append({
                'left': left_ms,
                'right': right_ms,
                'id': newSeg.id
            })
            count += 1
        models.db.session.commit()
        return segmentsMap, count

    def createSegments(self, segmentsMap, windowInfo, files=None):
        '''
            one of segmentsMap or windowInfo will be undefined
                if segmentsMap, then use windowInfo to create rolling segments of
                 the specified size and with the specific stride
                if windowInfo, then use segmentsMap to create segments of the
                 specified left and right timestamps
        '''
        if (segmentsMap):
            return self._createSegmentsCustom(segmentsMap)
        else:
            return self._createSegmentsWindows(windowInfo, files)

    def _deleteCustomSegments(self):
        allWindows = models.Segment.query.filter_by(project_id=self.id, type="CUSTOM").all()
        if (len(allWindows) > 0):
            for window in allWindows:
                models.db.session.delete(window)
            models.db.session.commit()

    def _deleteWindowSegments(self):
        allWindows = models.Segment.query.filter_by(project_id=self.id, type="WINDOW").all()
        if (len(allWindows) > 0):
            for window in allWindows:
                models.db.session.delete(window)
            models.db.session.commit()

    def _createSegmentsWindows(self, windowInfo, files=None):
        self._deleteWindowSegments()
        beforeNum = len(models.Segment.query.filter_by(project_id=self.id).all())
        newSegments=list()
        segmentsMap = dict() #where we're going to store the segments so they can be rendered

        windowSize_ms = windowInfo['window_size_ms']
        windowSlide_ms = windowInfo['window_roll_ms']
        if (files == None):
            files = self.files
        for file in files:
            series = file.series[0]
            seriesData = series.getFullOutput().get('data')

            segmentsMap[file.name] = {series.id:list()}

            windowStart_ms = seriesData[0][0] * 1000
            windowEnd_ms = windowStart_ms + windowSize_ms
            lastTimestamp_ms = seriesData[-1][0] * 1000
            while (windowEnd_ms < lastTimestamp_ms):
                newSegment = models.Segment(
                    project_id=self.id,
                    file_id=file.id,
                    series=series.id,
                    left=windowStart_ms,
                    right=windowEnd_ms,
                    type="WINDOW",
                    window_size_ms=windowSize_ms,
                    window_roll_ms=windowSlide_ms
                )
                newSegments.append(newSegment)
                models.db.session.add(newSegment)
                models.db.session.commit()
                segmentsMap[file.name][series.id].append({'id':newSegment.id, 'left':windowStart_ms,'right':windowEnd_ms})

                windowStart_ms += windowSlide_ms
                windowEnd_ms += windowSlide_ms
        afterNum = len(models.Segment.query.filter_by(project_id=self.id).all())

        success = (afterNum-beforeNum)==len(newSegments)
        return segmentsMap, success, len(newSegments)

    def _createSegmentsCustom(self, segmentsMap):
        beforeNum = len(models.Segment.query.filter_by(project_id=self.id).all())
        '''
        segmentsMap expected to be of form:
            { fId1: { seriesId1: [{'left': left1, 'right': right1},
                                  {'left': left2, 'right': right2}
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
                    left, right = span['left'], span['right']
                    newSegment = models.Segment(
                        project_id=self.id,
                        file_id=self.getFileByName(filename).id,
                        series=seriesId,
                        left=left,
                        right=right,
                        type="CUSTOM"
                    )
                    newSegments.append(newSegment)
                    models.db.session.add(newSegment)

                    span['id'] = newSegment.id
        models.db.session.commit()
        afterNum = len(models.Segment.query.filter_by(project_id=self.id).all())
        success = (afterNum-beforeNum)==len(newSegments)
        return segmentsMap, success, len(newSegments)

    def getSeriesOfInterest(self, file):
        supervisorModule = models.SupervisorModule.query.filter_by(project_id=self.id).first()
        if (supervisorModule):
            for s in file.series:
                if (s.id == supervisorModule.series_of_interest):
                    return s
        else:
            return file.series[0]

    def getSeriesToRender(self, file):
        supervisorModule = models.SupervisorModule.query.filter_by(project_id=self.id).first()
        if (supervisorModule):
            for s in file.series:
                if (s.id == supervisorModule.series_to_render):
                    return s
        else:
            return file.series[0]

    def getLFCode(self, lfNames, lfModule, thresholds, labels):
        i = 0
        s = None
        while (not s):
            s = self.getSeriesOfInterest(self.files[i])
            i += 1
        curSeries = s.getFullOutput().get('data')
        curSeries = np.array([x[-1] for x in curSeries])
        filledNaNs = None
        if np.sum(np.isnan(curSeries)) > 0:
            filledNaNs = curSeries.isna().to_numpy()
            curSeries = curSeries.fillna(0)

        series = curSeries.reshape((-1, 1))

        # apply lfs to series
        currentLfModule = lfModule(series, filledNaNs, thresholds, labels=labels)
        namesToCode = dict()
        import inspect
        for lfName in lfNames:
            try:
                lf = getattr(currentLfModule, lfName)
                namesToCode[lfName] = inspect.getsource(lf)
            except:
                continue
        return namesToCode

    def getLFStats(self, type='CUSTOM'):
        lfModule = self.getLFModule()
        lfs = list(map(lambda x: models.Labeler.query.filter_by(project_id=self.id, title=x).first(), lfModule.get_LF_names()))
        res = dict()
        for labeler in lfs:
            statsDict = {
                'coverage': None,
                'overlaps': 0,
                'conflicts': 0
            }
            #coverage
            nonAbstains = len(list(filter(lambda v: v.category.label != 'ABSTAIN', labeler.votes)))
            statsDict['coverage'] = nonAbstains / len(labeler.votes)
            res[labeler.title] = statsDict

        allSegments = models.Segment.query.filter_by(project_id=self.id, type=type).all()
        for segment in allSegments:
            #create presentVotes
            presentVotes = Counter()
            for vote in segment.votes:
                if (vote.category.label != 'ABSTAIN'):
                    presentVotes[vote.category.label] += 1
            for labeler in lfs:
                thisVote = models.Vote.query.filter_by(project_id=self.id, labeler_id=labeler.id, segment_id=segment.id).first()
                if (thisVote==None):
                    continue
                curLabel = thisVote.category.label
                if curLabel == 'ABSTAIN':
                    continue #if a labeler doesn't vote then it can't conflict or overlap
                #overlaps
                if curLabel in presentVotes and presentVotes[curLabel] > 1:
                    res[labeler.title]['overlaps'] += 1
                #conflicts
                for label in presentVotes.keys():
                    if label != curLabel:
                        #then some labeler votes something other than what this labeler does
                        res[labeler.title]['conflicts'] += 1

        for l in res.keys():
            res[l]['overlaps'] /= len(allSegments)
            res[l]['conflicts'] /= len(allSegments)
        return res

    def getLFModule(self, module='diagnoseEEG'):
        replacementMod = models.SupervisorModule.query.filter_by(project_id=self.id).first()
        if (replacementMod):
            module = replacementMod.title
        labelingFunctionModuleSpec = importlib.util.spec_from_file_location(module, f"./assets/afib_assets/{module}.py")
        labelingFunctionModule = importlib.util.module_from_spec(labelingFunctionModuleSpec)
        labelingFunctionModuleSpec.loader.exec_module(labelingFunctionModule)
        lfModule = getattr(labelingFunctionModule, module)
        return lfModule

    def populateInitialSupervisorValuesToDict(self, fileIds, d, lfModule="diagnoseEEG", timeSegment=None):
        lfModule = self.getLFModule(lfModule)

        labels = lfModule.getLabels()
        #### end of copied vars

        labelerNamesToIds = dict()
        categoryNamesToIds = dict()

        numLabelersInDb = len(models.Labeler.query.filter_by(project_id=self.id).all())
        shouldConstructLabelers = numLabelersInDb != len(lfModule.get_LF_names())

        shouldConstructThresholds = len(models.Threshold.query.filter_by(project_id=self.id).all()) == 0
        shouldConstructCategories = len(models.Category.query.filter_by(project_id=self.id).all()) != len(labels)
        if (shouldConstructCategories):
            print(f'Constructing the following categories: {labels.keys()}')
            #delete old labels and votes
            self.deleteVotes()
            for c in models.Category.query.filter_by(project_id=self.id).all():
                models.db.session.delete(c)
            # add new ones
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
            for c in models.Labeler.query.filter_by(project_id=self.id).all():
                models.db.session.delete(c)
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

        thresholds = lfModule.getInitialThresholds()

        d['labeling_function_titles'] = lfNames
        d['labeling_function_possible_votes'] = list(labels.keys())
        d['labelers_to_thresholds'] = lfModule.getThresholdsForLabelers()
        d['number_to_labels'] = lfModule.number_to_label_map()
        namesToCode = self.getLFCode(lfNames, lfModule, thresholds, labels)
        d['labeler_code'] = namesToCode
        i = 0
        s = None
        while (not s):
            s = self.getSeriesToRender(self.files[i])
            i += 1
        d['series_to_render_id'] = s.id

        return lfNames, list(labels.keys())

    def getThresholdsPayload(self):
        thresholds = models.Threshold.query.filter_by(project_id=self.id).all()
        thresholds = dict(map(lambda x: (x.title, x.value), thresholds))
        return thresholds

    def updateThreshold(self, threshold):
        title, value = threshold['title'], float(threshold['value'])
        thresh = models.Threshold.query.filter_by(project_id=self.id, title=title).first()
        thresh.value = value
        models.db.session.commit()
        return math.isclose(thresh.value,value)

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
                #continue
                # TODO(gus): Do something else with this? Like set error state in the database entry and display in GUI?

            # Instantiate the file class, and attach to this project instance
            self.files.append(File(self, fileDBModel.id, origFilePathObj, procFilePathObj))

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
                        newFileClassInstance = File(self, -1, newOrigFilePathObj, newProcFilePathObj)
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
