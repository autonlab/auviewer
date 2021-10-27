from .model import SimpleFeaturizer, FeaturizerParameter


class ExampleFeaturizer(SimpleFeaturizer):

    id = 'example'
    name = 'Example'
    parameters = [
        FeaturizerParameter(id='booleanr', name="Boolean Req'd", description="Boolean description", data_type='boolean', required=True),
        FeaturizerParameter(id='booleannr', name="Boolean Not Req'd", description="Boolean description", data_type='boolean', required=False),
        FeaturizerParameter(id='input', name="Input"),
        FeaturizerParameter(id='dropdown', name="Dropdown", description="Dropdown description", form_field_type='dropdown', options={'val1': 'Value 1', 'val2': 'Value 2'}),
        FeaturizerParameter(id='textarea', name='Textarea', description="Textarea description", form_field_type='textarea'),
        FeaturizerParameter(id='checkbox', name='Checkbox', description="Checkbox description", form_field_type='checkbox'),
        FeaturizerParameter(id='radio', name='Radio', description="Radio description", form_field_type='radio', options={'val1': 'Value 1', 'val2': 'Value 2', 'val3': 'Value 3'}),
        # FeaturizerParameter(id='', description="", data_type='slider'),
    ]
    neededSeries = 2

    def featurize(self, data, params):
        print(f"Parameters received:\n{params}")
        return data.mean()