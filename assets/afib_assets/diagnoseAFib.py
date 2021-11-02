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
            'SINUS': 1
        }

    @staticmethod
    def getThresholdsForLabelers():
        return {
            "variation_h": ["max_coefficient_of_variation"],
            "iqr_h": ["max_interquartile_range"],
            "range_h": ["max_range"],
            "std_h": ["max_standard_deviation"],
            "variation_l": ["min_coefficient_of_variation"],
            "iqr_l": ["min_interquartile_range"],
            "range_l": ["min_range"],
            "std_l": ["min_standard_deviation"]
        }

    @staticmethod
    def get_LF_names():
        return [
            'variation_h',
            'iqr_h',
            'range_h',
            'std_h',
            'variation_l',
            'iqr_l',
            'range_l',
            'std_l'
        ]

    @staticmethod
    def number_to_label_map():
        return {
            -1: 'ABSTAIN',
            0: 'ATRIAL_FIBRILLATION',
            1: 'SINUS'
        }
    def get_numbers_vector(self):
        return [
            self.variation(compute=True),
            self.iqr(compute=True),
            self.range(compute=True),
            self.std(compute=True)
            ]
    def get_vote_vector(self):
        return [
            self.variation_h(),
            self.iqr_h(),
            self.range_h(),
            self.std_h(),
            self.variation_l(),
            self.iqr_l(),
            self.range_l(),
            self.std_l()
            ]

    def variation_h(self, compute=False):
        if (self.cov > self.thresholds['max_coefficient_of_variation']):
            return self.ATRIAL_FIBRILLATION
        else:
            return self.ABSTAIN

    def variation_l(self, compute=False):
        if (self.cov < self.thresholds['min_coefficient_of_variation']):
            return self.SINUS
        else:
            return self.ABSTAIN

    def iqr_h(self, compute=False):
        if self.iqr > self.thresholds['max_interquartile_range']:
            return self.ATRIAL_FIBRILLATION
        else:
            return self.ABSTAIN

    def iqr_l(self, compute=False):
        if self.iqr < self.thresholds['min_interquartile_range']:
            return self.SINUS
        else:
            return self.ABSTAIN

    def std_h(self, compute=False):
        if self.std > self.thresholds['max_standard_deviation']:
            return self.ATRIAL_FIBRILLATION
        else:
            return self.ABSTAIN

    def std_l(self, compute=False):
        if self.std < self.thresholds['min_standard_deviation']:
            return self.SINUS
        else:
            return self.ABSTAIN

    def range_h(self, compute=False):
        if self.range > self.thresholds['max_range']:
            return self.ATRIAL_FIBRILLATION
        else:
            return self.ABSTAIN

    def range_l(self, compute=False):
        if self.range < self.thresholds['min_range']:
            return self.SINUS
        else:
            return self.ABSTAIN