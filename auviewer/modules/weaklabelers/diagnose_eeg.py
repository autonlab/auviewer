import numpy as np
from scipy.stats.mstats import winsorize
from sklearn.linear_model import LinearRegression
from sklearn import linear_model
from sklearn.mixture import GaussianMixture
import scipy
from scipy.signal import find_peaks

DESCRIPTION = {
    'S1': "High shaggy aEEG baseline (constantly at 4-200 mV).",
    'S2': "Low aEEG baseline continually at low amplitude <= 2-3 mV.",
    'S3': "aEEG baseline never falls to near-zero (< 1mV).",
    'S4': "Abrupt, recurring and high amplitude (> 7.5 mV) spikes.",
    'S5': "spiky aEEG with higher baseline but frequent and abrupt falls to near-zero"
}


class diagnoseEEG:
    def __init__(self, EEG, filledNaNs, thresholds, labels, verbose=True, explain=True):
        self.ABSTAIN = labels['ABSTAIN']
        self.NORMAL = labels['NORMAL']
        self.SUPPRESSED = labels['SUPPRESSED']
        self.SUPPRESSED_WITH_ICTAL = labels['SUPPRESSED_WITH_ICTAL']
        self.BURST_SUPRESSION = labels['BURST_SUPRESSION']

        self.EEG = EEG
        self.length_EEG = len(EEG)
        self.filledNaNs = filledNaNs
        filledNaNs = np.logical_and(self.EEG < 50, filledNaNs)  # Maximum aEEG value 50 mV
        if self.filledNaNs is not None:
            self.EEG = self.EEG[~self.filledNaNs]  # Keep only not NaN indices
        else:
            self.EEG = self.EEG
        self.EEG = winsorize(a=self.EEG, limits=[0.01, 0.01], inplace=False)  # To remove artefacts
        self.thresholds = thresholds
        self.NoBaseline = False
        self.verbose = verbose
        self.explain = explain
        self.means = []
        self.weights = []
        self.bic = []

        self.description = DESCRIPTION
        self.slope, self.intial_EEG_baseline, _, self.y_pred = _fitRobustLine(self.EEG)
        self.final_EEG_baseline = float(self.y_pred[-1])
        self.average_EEG_baseline = np.sum(self.y_pred) / len(self.y_pred)
        self.peaks, _ = find_peaks(self.EEG.reshape((-1,)), prominence=2, width=1)
        self.prominences = self.EEG[self.peaks].reshape((-1,)) - self.y_pred.reshape((-1,))[self.peaks]

        # Number of high and low amplitude peaks
        if len(self.peaks) > 0:  # There may be no peaks at all
            self.n_peaks_VHA = len(self.peaks[self.prominences > self.thresholds['EEG__HIGH_15']])
            self.n_peaks_HA = len(self.peaks[self.prominences > self.thresholds['EEG__HIGH_10']])
            self.n_peaks_LA = len(self.peaks[self.prominences > self.thresholds['EEG__HIGH_5']]) - self.n_peaks_HA
        else:
            self.n_peaks_VHA = 0
            self.n_peaks_HA = 0
            self.n_peaks_LA = 0

        self.many_high_amp_spikes = self.n_peaks_HA > self.thresholds['n_high_amplitude_peaks_per_hour']
        self.many_low_amp_spikes = self.n_peaks_LA > self.thresholds['n_high_amplitude_peaks_per_hour']
        self.low_baseline = self.average_EEG_baseline < self.thresholds['EEG__LOW']
        self.dur_low_amplitude_EEG = len(self.EEG[self.EEG < self.thresholds['near_zero']])

        # Fit Gaussian Mixtures
        for n_components in [1, 2]:
            obj = GaussianMixture(n_components=n_components)
            obj.fit(self.EEG)
            self.bic.append(obj.bic(self.EEG))
            self.weights.append(obj.weights_.squeeze())
            self.means.append(obj.means_.squeeze())

        if self.verbose:
            self.print_statistics()

    def print_statistics(self):
        """
        Prints decision making statistics
        """
        print('\t #############')
        print(
            f'\t Slope: {np.around(float(self.slope), 3)}  y-intercept: {np.around(float(self.intial_EEG_baseline), 3)}')
        print(f'\t Average EEG baseline: {np.around(self.average_EEG_baseline, 3)}')
        print(f'\t NaN time period: {np.sum(self.filledNaNs)}')
        print(f'\t Peaks (> 5mV): {len(self.peaks)}')
        print(f'\t 1-component GMM: means = {self.means[0]} | weights = {self.weights[0]} BIC = {self.bic[0]}')
        print(f'\t 2-component GMM: means = {self.means[1]} | weights = {self.weights[1]} BIC = {self.bic[1]}')
        print(f"\t Number of high amplitude (> {self.thresholds['EEG__HIGH_10']} mV) peaks {self.n_peaks_HA}")
        print(f"\t Number of low amplitude ({self.thresholds['EEG__HIGH_5']} < _ < 10 mV) peaks {self.n_peaks_LA}")
        print(f'\t Duration of near-zero aEEG amplitude (< 1mV): {self.dur_low_amplitude_EEG}')
        print(f'\t Not-NaNs EEG signal length: {len(self.EEG)} \n\t Minimum EEG value: {min(self.EEG)}')
        print('\t #############')

    def high_aEEG_baseline_NORMAL(self, threshold_EEG_HIGH=10):
        """
        High shaggy aEEG baseline constantly at an amplitude of around 10-20 mV, then NORMAL EEG.
        """
        if ((self.average_EEG_baseline >= threshold_EEG_HIGH) and (not self.NoBaseline)):
            return self.NORMAL
        else:
            return self.ABSTAIN

    def unimodal_aEEG_NORMAL(self):
        if (min(self.weights[1]) < 0.05) and (self.means[0] > self.thresholds['EEG__LOW']):  # Unimodal distribution
            return self.NORMAL
        else:
            return self.ABSTAIN

    def unimodal_aEEG_SUPPRESSED(self):
        if (min(self.weights[1]) < 0.05) and (self.means[0] < self.thresholds['EEG__LOW']):  # Unimodal distribution
            return self.SUPPRESSED
        else:
            return self.ABSTAIN

    def bimodal_aEEG_SUPPRESSED(self):
        if (min(self.weights[1]) > 0.05) and np.max(self.means[1]) < self.thresholds['EEG__LOW']:
            return self.SUPPRESSED
        else:
            return self.ABSTAIN

    def bimodal_aEEG_SUPPRESSED_WITH_ICTAL(self):
        if (min(self.weights[1]) > 0.05) and (np.min(self.means[1]) < self.thresholds['EEG__LOW']) and (
                np.max(self.means[1]) > self.thresholds['EEG__HIGH_5']):
            return self.SUPPRESSED_WITH_ICTAL
        else:
            return self.ABSTAIN

    def bimodal_aEEG_BURST_SUPRESSION(self):
        if (min(self.weights[1]) > 0.05) and (np.min(self.means[1]) < self.thresholds['EEG__LOW']) and (
                np.max(self.means[1]) < self.thresholds['EEG__HIGH_5']):
            return self.BURST_SUPRESSION
        else:
            return self.ABSTAIN

    def bimodal_aEEG_NORMAL(self):
        if (min(self.weights[1]) > 0.05) and np.min(self.means[1]) > self.thresholds['EEG__LOW']:
            return self.NORMAL
        else:
            return self.ABSTAIN

    def bimodal_aEEG(self):
        if min(self.weights[1]) > 0.05:
            if np.max(self.means[1]) < self.thresholds['EEG__LOW']:
                return self.SUPPRESSED
            elif (np.min(self.means[1]) < self.thresholds['EEG__LOW']) and (
                    np.max(self.means[1]) > self.thresholds['EEG__HIGH_5']):
                return self.SUPPRESSED_WITH_ICTAL
            elif (np.min(self.means[1]) < self.thresholds['EEG__LOW']) and (
                    np.max(self.means[1]) < self.thresholds['EEG__HIGH_5']):
                return self.BURST_SUPRESSION
            elif np.min(self.means[1]) > self.thresholds['EEG__LOW']:
                return self.NORMAL
            else:
                return self.ABSTAIN
        else:  # Unimodal distribution
            if self.means[0] < self.thresholds['EEG__LOW']:
                return self.SUPPRESSED
            if self.means[0] > self.thresholds['EEG__LOW']:
                return self.NORMAL
            else:
                return self.ABSTAIN

    def aEEG_NOT_near_zero_NORMAL(self):
        if (np.sum(self.EEG <= self.thresholds['near_zero']) < self.thresholds['near_zero_duration_tol']):
            return self.NORMAL
        else:
            return self.ABSTAIN

    def very_spiky_aEEG_SUPPRESSED_WITH_ICTAL(self):
        """
        aEEF having spikes having > 15 mV more than once every minutes on an average is most probably ictal.
        """
        if self.n_peaks_VHA > self.thresholds['n_high_amplitude_peaks_per_hour']:
            return self.SUPPRESSED_WITH_ICTAL
        else:
            return self.ABSTAIN

    def well_separated_aEEG_modes_SUPPRESSED_WITH_ICTAL(self):
        """
        If aEEG values are well separated, i.e. their distribution has two peaks separated by atleast 4mV,
        then the aEEG is more likey to be Supressed with ictal
        """
        if abs(self.means[1][0] - self.means[1][1]) > self.thresholds['min_separation'] and min(self.weights[1]) > 0.05:
            return self.SUPPRESSED_WITH_ICTAL
        else:
            return self.ABSTAIN

    def low_baseline_SUPPRESSED_WITH_ICTAL(self):
        if (not self.NoBaseline) and (self.low_baseline) and (self.many_high_amp_spikes):
            return self.SUPPRESSED_WITH_ICTAL
        else:
            return self.ABSTAIN

    def low_baseline_BURST_SUPRESSION(self):
        if (not self.NoBaseline) and (self.low_baseline) and (self.many_low_amp_spikes):
            return self.SUPPRESSED_WITH_ICTAL
        else:
            return self.ABSTAIN

    def low_baseline_SUPPRESSED(self):
        if (not self.NoBaseline) and (self.low_baseline) and (not self.many_high_amp_spikes) and (
        not self.many_low_amp_spikes):
            return self.SUPPRESSED
        else:
            return self.ABSTAIN

    def low_baseline_aEEG(self):
        if self.NoBaseline:
            return self.ABSTAIN
        if self.low_baseline:
            if self.many_high_amp_spikes:
                return self.SUPPRESSED_WITH_ICTAL
            elif self.many_low_amp_spikes:
                return self.BURST_SUPRESSION
            else:
                return self.SUPPRESSED
        else:
            return self.ABSTAIN

    def high_baseline_infrequent_drops_NORMAL(self):
        if (not self.NoBaseline) and (not self.low_baseline) and (
                self.dur_low_amplitude_EEG <= self.thresholds['near_zero_duration_tol']):
            return self.NORMAL
        else:
            return self.ABSTAIN

    def high_baseline_frequent_drops_SUPPRESSED_WITH_ICTAL(self):
        if (not self.NoBaseline) and (not self.low_baseline) and (
                self.dur_low_amplitude_EEG > self.thresholds['near_zero_duration_tol']) and (
                self.bimodal_aEEG_BURST_SUPRESSION() != self.BURST_SUPRESSION):
            return self.SUPPRESSED_WITH_ICTAL
        else:
            return self.ABSTAIN

    def high_baseline_frequent_drops_BURST_SUPRESSION(self):
        if (not self.NoBaseline) and (not self.low_baseline) and (
                self.dur_low_amplitude_EEG > self.thresholds['near_zero_duration_tol']) and (
                self.bimodal_aEEG_BURST_SUPRESSION() == self.BURST_SUPRESSION):
            return self.BURST_SUPRESSION
        else:
            return self.ABSTAIN

    def high_baseline_frequent_drops(self):
        if self.NoBaseline:
            return self.ABSTAIN
        if not self.low_baseline:
            if self.dur_low_amplitude_EEG <= self.thresholds['near_zero_duration_tol']:
                return self.NORMAL
            elif self.dur_low_amplitude_EEG > self.thresholds[
                'near_zero_duration_tol'] and self.bimodal_aEEG_BURST_SUPRESSION() == self.BURST_SUPRESSION:
                return self.BURST_SUPRESSION
            else:
                return self.SUPPRESSED_WITH_ICTAL
        else:
            return self.ABSTAIN

    def get_vote_vector(self):
        return [self.bimodal_aEEG(), self.low_baseline_aEEG(), self.high_baseline_frequent_drops(),
                self.very_spiky_aEEG_SUPPRESSED_WITH_ICTAL(), self.well_separated_aEEG_modes_SUPPRESSED_WITH_ICTAL(),
                self.aEEG_NOT_near_zero_NORMAL(), self.high_aEEG_baseline_NORMAL(threshold_EEG_HIGH=4),
                self.high_aEEG_baseline_NORMAL(threshold_EEG_HIGH=10), self.unimodal_aEEG_NORMAL(),
                self.unimodal_aEEG_SUPPRESSED(), self.bimodal_aEEG_SUPPRESSED(),
                self.bimodal_aEEG_SUPPRESSED_WITH_ICTAL(),
                self.bimodal_aEEG_BURST_SUPRESSION(), self.bimodal_aEEG_NORMAL(),
                self.low_baseline_SUPPRESSED_WITH_ICTAL(),
                self.low_baseline_BURST_SUPRESSION(), self.low_baseline_SUPPRESSED(),
                self.high_baseline_infrequent_drops_NORMAL(),
                self.high_baseline_frequent_drops_SUPPRESSED_WITH_ICTAL(),
                self.high_baseline_frequent_drops_BURST_SUPRESSION()]

    @staticmethod
    def get_LF_names():
        return ['bimodal_aEEG', 'low_baseline_aEEG', 'high_baseline_frequent_drops',
                'very_spiky_aEEG_SUPPRESSED_WITH_ICTAL',
                'well_separated_aEEG_modes_SUPPRESSED_WITH_ICTAL', 'aEEG_NOT_near_zero_NORMAL',
                'high_aEEG_baseline_NORMAL_4', 'high_aEEG_baseline_NORMAL_10',
                'unimodal_aEEG_NORMAL', 'unimodal_aEEG_SUPPRESSED', 'bimodal_aEEG_SUPPRESSED',
                'bimodal_aEEG_SUPPRESSED_WITH_ICTAL',
                'bimodal_aEEG_BURST_SUPRESSION', 'bimodal_aEEG_NORMAL', 'low_baseline_SUPPRESSED_WITH_ICTAL',
                'low_baseline_BURST_SUPRESSION', 'low_baseline_SUPPRESSED', 'high_baseline_infrequent_drops_NORMAL',
                'high_baseline_frequent_drops_SUPPRESSED_WITH_ICTAL', 'high_baseline_frequent_drops_BURST_SUPRESSION']


def _fitRobustLine(T):
    # T is a time series
    """
    Fit the RANSAC robust linear regressor
    Returns:
    Coefficient, intercept, coefficient of determination (R^2) and predicted line
    """

    ransac = linear_model.RANSACRegressor(base_estimator=linear_model.Ridge(alpha=1000))
    # ransac = linear_model.RANSACRegressor()
    ransac.fit(np.arange(len(T)).reshape((-1, 1)), T)
    y = ransac.predict(np.arange(len(T)).reshape((-1, 1)))

    return ransac.estimator_.coef_, ransac.estimator_.intercept_, ransac.estimator_.score(y, T), y

## Labelling functions
# obj.bimodal_aEEG()
# obj.low_baseline_aEEG()
# obj.high_baseline_frequent_drops()
# obj.very_spiky_aEEG_SUPPRESSED_WITH_ICTAL()
# obj.well_separated_aEEG_modes_SUPPRESSED_WITH_ICTAL()
# obj.aEEG_NOT_near_zero_NORMAL()
# obj.high_aEEG_baseline_NORMAL(threshold_EEG_HIGH = 4)
# obj.high_aEEG_baseline_NORMAL(threshold_EEG_HIGH = 10)
# obj.unimodal_aEEG_NORMAL()
# obj.unimodal_aEEG_SUPPRESSED()
# obj.bimodal_aEEG_SUPPRESSED()
# obj.bimodal_aEEG_SUPPRESSED_WITH_ICTAL()
# obj.bimodal_aEEG_BURST_SUPRESSION()
# obj.bimodal_aEEG_NORMAL()
# obj.low_baseline_SUPPRESSED_WITH_ICTAL()
# obj.low_baseline_BURST_SUPRESSION()
# obj.low_baseline_SUPPRESSED()
# obj.high_baseline_infrequent_drops_NORMAL()
# obj.high_baseline_frequent_drops_SUPPRESSED_WITH_ICTAL()
# obj.high_baseline_frequent_drops_BURST_SUPRESSION()