from .model import SimpleFeaturizer, FeaturizerParameter


class MeanFeaturizer(SimpleFeaturizer):

    id = 'mean'
    name = 'Mean'
    parameters = [
        FeaturizerParameter(id='skipna', name="Skip NaN", description="Skip NaN values", data_type='boolean'),
        FeaturizerParameter(id='input', name="An Input Field"),
        FeaturizerParameter(id='dropdown', name="Dropdown", description="", form_field_type='dropdown', options={'val1': 'Value 1', 'val2': 'Value 2'}),
        FeaturizerParameter(id='textarea', name='Textarea', description="", form_field_type='textarea'),
        FeaturizerParameter(id='checkbox', name='Checkbox', description="", form_field_type='checkbox'),
        FeaturizerParameter(id='radio', name='Radio', description="", form_field_type='radio', options={'val1': 'Value 1', 'val2': 'Value 2', 'val3': 'Value 3'}),
        # FeaturizerParameter(id='', description="", data_type='slider'),
    ]

    def featurize(self, data, params):
        print(f"Parameters received:\n{params}")
        return data.mean()
