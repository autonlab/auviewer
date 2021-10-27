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