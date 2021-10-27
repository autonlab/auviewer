from .model import SimpleFeaturizer, FeaturizerParameter


class MeanFeaturizer(SimpleFeaturizer):

    id = 'mean'
    name = 'Mean'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]
    neededSeries = 2

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return data.mean(skipna=skipna)