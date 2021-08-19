from abc import ABC, abstractmethod
from typing import AnyStr, List, Dict, Optional, Union

class WeakLabelModel():

    def __init__(self):
        self.fields = [
            {
                WeakLabelerParameter(
                    id='baseline_threshold',
                    name='Baseline Threshold',
                )
            },
        ]

        # TODO: somewhere in here, make sure that the global parameter
        # becomes the default parameter of weak labeling functions,
        # if it exists globally

class WeakLabeler(ABC):

    def __init__(self):

        # TODO
        # check for required fields (name, fields if present is list, features_required if present is list (otherwise init as empty lists)

    # will be provided a numpy array of dimension n x m.
    def vote(arr):
        """

        :return:
        """
        raise NotImplementedError("Error! Required weak labeler method vote() not implemented.")


class WeakLabelerParameter():

    def __init__(self, name, description='', data_type='', form_field_type='', options=[]):

        valid_data_types = ['numeric', 'text']
        # TODO: validate against above

        valid_form_field_types = ['input', 'textarea', 'checkbox', 'radio', 'slider']
        # TODO: validate against above

        # TODO: lots of validation left to do

    def validate(self):

        # TODO: validate if numeric here. might also do e.g. sql injection checking here.