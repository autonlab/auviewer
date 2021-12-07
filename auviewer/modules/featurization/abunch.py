from .model import SimpleFeaturizer, FeaturizerParameter

class CoeffOfVariationFeaturizer(SimpleFeaturizer):

    id = 'cv'
    name = 'Coefficient of Variation'
    description = 'Coefficient of variation is the mean over the standard deviation.'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return data.mean(skipna=skipna)/data.std(skipna=skipna)

class MADFeaturizer(SimpleFeaturizer):

    id = 'mad'
    name = 'Median of Absolute Deviation from Mean'

    def featurize(self, data, params={}):
        # TODO(gus): Add skipna?
        return (data - data.mean()).abs().median()

class NFeaturizer(SimpleFeaturizer):

    id = 'n'
    name = 'Value Count (n)'

    def featurize(self, data, params={}):
        # TODO(gus): Add ability to skipna
        return data.shape[0]

class MinFeaturizer(SimpleFeaturizer):

    id = 'min'
    name = 'Min'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return data.min(skipna=skipna)

class MaxFeaturizer(SimpleFeaturizer):

    id = 'max'
    name = 'Max'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return data.max(skipna=skipna)

class MedianFeaturizer(SimpleFeaturizer):

    id = 'median'
    name = 'Median'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return data.median(skipna=skipna)

class RangeFeaturizer(SimpleFeaturizer):

    id = 'range'
    name = 'Range'
    description = 'Range is max minus min.'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return data.max(skipna=skipna) - data.min(skipna=skipna)

class RangeRatioFeaturizer(SimpleFeaturizer):

    id = 'rangeratio'
    name = 'Range Ratio (range / median)'
    description = 'Range ratio is the range over median.'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return (data.max(skipna=skipna) - data.min(skipna=skipna)) / data.median(skipna=skipna)

class DataDenFeaturizer(SimpleFeaturizer):

    id = 'dataden'
    name = 'Data Density'
    description = 'Data density is the number of values (n) over the window size in seconds'

    def featurize(self, data, params={}):
        # TODO(gus): Add ability to skipna
        # TODO(gus): Move this exception handling to outer base class
        try:
            return data.shape[0] / (data.index[-1].timestamp() - data.index[0].timestamp())
        except:
            return None

from sklearn.linear_model import LinearRegression
slrm = LinearRegression()
class LRSlopeFeaturizer(SimpleFeaturizer):

    id = 'skl_slope'
    name = 'Linear Regression Slope (sklearn)'
    description = 'Slope of linear regression computed with sklearn.LinearRegression'

    def featurize(self, data, params={}):
        # TODO(gus): Move this exception handling to outer base class
        try:
            slrm.fit(data.reset_index()[['time']], data)
            return slrm.coef_[0]
        except:
            return None



### BELOW HERE NEEDS TESTING


class MaxGapFeaturizer(SimpleFeaturizer):

    id = 'maxgap'
    name = 'Max Gap'
    description = 'Maximum timestamp gap between two subsequent measurements'

    def featurize(self, data, params={}):
        # TODO(gus): Move this exception handling to outer base class
        try:
            return data.index.diff().max()
        except:
            return None



import rpy2
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.packages import importr
robjects.r['source']('temp.R')

import numpy as np
class RobustSlopeFeaturizer(SimpleFeaturizer):

    id = 'robustslope'
    name = 'Robst Slope (R)'
    description = 'Slope from the robust linear regression fit using M estimator (uses R)'

    def featurize(self, data, params={}):
        with localconverter(robjects.default_converter + pandas2ri.converter):
            # ret = robjects.r['get_robust_slope'](data.index, data['value'])
            # ret = robjects.r['get_robust_slope'](data.reset_index()['time'].values.astype(np.int64) // 10 ** 9, data)

            data = data.reset_index() # data.reset_index(inplace=True)
            data['time'] = data['time'].astype(np.int64) // 10**9



            # t = data.reset_index()[['time']]
            # t['time'] = t['time'].astype(np.int64) // 10**9
            # data['time'] = t['time']
            # print(t)
            print('arg1')
            print(data['time'])
            print('arg2')
            print(data['value'])
            # ret = robjects.r['get_robust_slope'](data[['time']], data.set_index('time'))
            ret = robjects.r['get_robust_slope'](data['time'], data['value'])
        print(ret)
        print(ret[0])
        return None if isinstance(ret[0], rpy2.rinterface_lib.sexp.NALogicalType) else ret[0]