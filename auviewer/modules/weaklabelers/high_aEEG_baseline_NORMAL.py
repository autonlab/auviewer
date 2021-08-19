from auviewer.modules.weaklabelers.model import WeakLabeler, WeakLabelerParameter

class high_aEEG_baseline_NORMAL(WeakLabeler):

    def __init__(self):
        self.name = "high_aEEG_baseline_NORMAL"
        self.description = ""
        self.fields = [
            {
                WeakLabelerParameter(
                    id='baseline_threshold',
                    name='Baseline Threshold',
                )
            },
        ]

        self.parent_model_fields_required = [...]

        self.features_required = [
            'auviewer.modules.featurizers.xyz1',
            'auviewer.modules.featurizers.xyz2',
        ]

    def vote(self, fields, features):
        # fields & features will be dict
        xyz1 = features['auviewer.modules.featurizers.xyz1']
        xyz2 = features['auviewer.modules.featurizers.xyz2']

        field1 = fields['baseline_threshold']