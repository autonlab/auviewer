from pandas.core import series
from scipy.stats import variation, iqr
import numpy as np
#coefficient of variation- scipy.stats.variation
#IQR - scipy.stats.iqr
#range - np.ptp (for peak to peak)
#stdev - np.std

class diagnoseAFib:
    def __init__(self, beatToBeatSeries, filledNaNs, thresholds=None, labels=None):
        self.ABSTAIN = labels['ABSTAIN']
        self.ATRIAL_FIBRILLATION = labels['ATRIAL_FIBRILLATION']
        self.SINUS = labels['SINUS']
        self.OTHER = labels['OTHER']
        if thresholds == None:
            thresholds = self.getInitialThresholds()

        self.cov = variation(beatToBeatSeries)
        self.range = np.ptp(beatToBeatSeries)
        self.std = np.std(beatToBeatSeries)
        self.iqr = iqr(beatToBeatSeries)
        # filledNaNs = np.logical_and(self.b2bSeries > 0, filledNaNs)
        # if filledNaNs is not None:
        #     self.b2bSeries = self.b2bSeries[~filledNaNs]

        self.thresholds = thresholds


    @staticmethod
    def getInitialThresholds():
        return {
            'max_coefficient_of_variation': .15,
            'min_coefficient_of_variation': .03,
            'max_interquartile_range': 15.0,
            'min_interquartile_range': 3.0,
            'max_standard_deviation': 8.0,
            'min_standard_deviation': 3.0,
            'max_range': 20.0,
            'min_range': 5.0
        }

    @staticmethod
    def getLabels():
        return {
            'ABSTAIN': -1,
            'ATRIAL_FIBRILLATION': 0,
            'SINUS': 1,
            'OTHER': 2
        }

    @staticmethod
    def getThresholdsForLabelers():
        return {
            "variationLabeler": ["max_coefficient_of_variation", "min_coefficient_of_variation"],
            "iqrLabeler": ["max_interquartile_range", "min_interquartile_range"],
            "rangeLabeler": ["max_range", "min_range"],
            "stdLabeler": ["max_standard_deviation", "min_standard_deviation"],
        }

    @staticmethod
    def get_LF_names():
        return [
            'variationLabeler',
            'iqrLabeler',
            'rangeLabeler',
            'stdLabeler',
        ]

    @staticmethod
    def number_to_label_map():
        return {
            -1: 'ABSTAIN',
            0: 'ATRIAL_FIBRILLATION',
            1: 'SINUS',
            2: 'OTHER'
        }
    def get_numbers_vector(self):
        return [
            self.variationLabeler(compute=True),
            self.iqrLabeler(compute=True),
            self.rangeLabeler(compute=True),
            self.stdLabeler(compute=True)
            ]
    def get_vote_vector(self):
        return [
            self.variationLabeler(),
            self.iqrLabeler(),
            self.rangeLabeler(),
            self.stdLabeler(),
            ]

    def variationLabeler(self, compute=False):
        if (self.cov > self.thresholds['max_coefficient_of_variation']):
            return self.ATRIAL_FIBRILLATION
        elif(self.cov < self.thresholds['max_coefficient_of_variation'] and
            self.cov > self.thresholds['min_coefficient_of_variation']):
            return self.OTHER
        elif (self.cov < self.thresholds['min_coefficient_of_variation']):
            return self.SINUS


    def iqrLabeler(self, compute=False):
        if self.iqr > self.thresholds['max_interquartile_range']:
            return self.ATRIAL_FIBRILLATION
        if (self.iqr < self.thresholds['max_interquartile_range'] and
            self.iqr > self.thresholds['min_interquartile_range']):
            return self.OTHER
        if self.iqr < self.thresholds['min_interquartile_range']:
            return self.SINUS
        
        return self.ABSTAIN

    def stdLabeler(self, compute=False):
        if self.std > self.thresholds['max_standard_deviation']:
            return self.ATRIAL_FIBRILLATION
        if (self.std < self.thresholds['max_standard_deviation'] and
            self.std > self.thresholds['min_standard_deviation']):
            return self.OTHER
        if self.std < self.thresholds['min_standard_deviation']:
            return self.SINUS
        
        return self.ABSTAIN

    def rangeLabeler(self, compute=False):
        if self.range > self.thresholds['max_range']:
            return self.ATRIAL_FIBRILLATION
        if (self.range < self.thresholds['max_range'] and
            self.range > self.thresholds['min_range']):
            return self.OTHER
        if self.range < self.thresholds['min_range']:
            return self.SINUS

        return self.ABSTAIN
