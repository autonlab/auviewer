from .model import SimpleFeaturizer, FeaturizerParameter

class StandardDeviationFeaturizer(SimpleFeaturizer):

    id = 'std'
    name = 'Standard Deviation'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
    ]

    def featurize(self, data, params={}):
        skipna = params['skipna']
        return data.std(skipna=skipna)
