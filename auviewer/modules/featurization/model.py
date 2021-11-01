from abc import ABC, abstractmethod
from typing import AnyStr, List, Dict, Optional, Union
from functools import partial

class AdvancedFeaturizer(ABC):
    pass

class SimpleFeaturizer(ABC):

    id = None
    parameters = []

    # def __init__(self, files: Union[str, List[str]], series: Union[str, List[str], None]):
    #
    #     # If a string was provided as the files param (i.e. referencing a single file), convert it to a list
    #     if isinstance(files, str):
    #         files = [files]
    #
    #     # If a string was provided as the series param (i.e. referencing a single series), convert it to a list
    #     if isinstance(series, str):
    #         series = [series]
    #
    #     # Set files & series as instance properties
    #     self.files = files
    #     self.series = series

    def __init__(self):
        if self.id is None:
            raise Exception("Featurizer has no ID.")
        if self.name is None:
            raise Exception(f"Featurizer {self.id} has no name.")

    def getFeaturizeFunction(self, params):
        # TODO(gus): Wrap iteratively in try/except?
        print(f"Params pre-process: {params}")
        preparedParams = self.prepareParams(params)
        print(f"Params post-process: {preparedParams}")
        return partial(self.featurize, params=preparedParams)

    def getFields(self):
        """
        Produces and returns a list of field dicts ready to be marshalled to JSON and supplied to Webix as a JavaScript
        array representing the featurizer's form fields.
        """
        return [field.getField() for field in self.parameters]

    @abstractmethod
    def featurize(self, data, params={}):
        """
        This will be the function which, given a Pandas DataFrame and parameters dict, featurizes and returns the
        feature's scalar value output.
        :return: Scalar value output of featurization
        """
        raise NotImplementedError("Error! Required featurizer method 'featurize' not implemented.")

    def prepareParams(self, params):
        """
        Returns a processed version of params given web form input.
        """
        newParams = {}
        for p in self.parameters:

            try:

                val = params[p.id]
                if p.data_type == 'boolean':
                    if val is None or val=='':
                        val = p.default
                    elif not val or val==0 or val=='0' or val=='false' or val=='False':
                        val = False
                    else:
                        val = True
                else:
                    if val is None or val=='':
                        val = p.default

                newParams[p.id] = val

            except:
                newParams[p.id] = p.default

        return newParams


class FeaturizerParameter():

    def __init__(self,
                 id,
                 name,
                 description='',
                 data_type='float',
                 form_field_type='input',
                 options=[],
                 required=True,
                 default=None,
                 ):
        """
        :param id: Parameter ID
        :param name: Name of the parameter
        :param description: Description of the parameter with usage instructions for users
        :param data_type: Indicates the data type of the parameter. Possible values are 'string', 'int', and 'float'.
        :param form_field_type: Indicates the type of form field to present to the user. Possible values are 'input',
        'dropdown', 'textarea', 'checkbox', 'radio', and 'slider'. Default value is 'input'. If data_type is 'boolean',
        then form_field_type and options are ignored.
        :param options: Dict (option value=>display value) of options available for user to choose from, if the
        form_field_type is 'dropdown'. If data_type is 'boolean', then form_field_type and options are ignored.
        :param required: Boolean indicating whether the parameter must be specified by the user.
        :param default: Specifies the default value to use for the parameter if a value is not specified by the user.
        :return: None
        """

        # Validation dictionaries
        valid_data_types = ['string', 'int', 'float', 'boolean']
        valid_form_field_types = ['input', 'dropdown', 'textarea', 'checkbox', 'radio', 'slider']

        # Validate properties
        if data_type not in valid_data_types:
            raise Exception(f"Invalid data_type provided: {data_type}")
        if form_field_type not in valid_form_field_types:
            raise Exception(f"Invalid form_field_type provided: {form_field_type}")
        if not len(name) > 0:
            raise Exception(f"Empty parameter name provided: {name}")

        # Boolean-specific properties enforcement
        if data_type == 'boolean':

            if required:
                form_field_type = 'checkbox'
                options = []
            else:
                form_field_type = 'dropdown'
                options = {'': '', 'true': 'True', 'false': 'False'}

            if not default:
                default = False
            else:
                default = True
            # TODO: TEMP!!!!!
            default = 'default'

        # Set properties
        self.id = id
        self.name = name
        self.description = description
        self.data_type = data_type
        self.form_field_type = form_field_type
        self.options = options
        self.required = required
        self.default = default

    def getField(self):
        """
        This function produces and returns a dict ready to be marshalled to JSON and
        then supplied to Webix as a JavaScript object representing a form field.
        """

        field = {
            'name': self.id,
            'id': self.id,
            #'labelWidth': 230,
            'labelWidth': 'auto',
            'labelAlign': 'left',
            'inputAlign': 'right',
            'label': self.name + ('*' if self.required else ''),
            'tooltip': self.description + (f"\n\nDefault value: {self.default}" if self.default is not None else ''),
        }

        if self.form_field_type in ('radio', 'textarea', 'checkbox'):
            field['view'] = self.form_field_type
            if self.default is not None:
                field['value'] = self.default
        elif self.form_field_type == 'dropdown':
            field['view'] = 'select'
        elif self.form_field_type == 'input':
            field['view'] = 'text'
        elif self.form_field_type == 'slider':
            raise NotImplementedError("Slider is not implemented.")
        else:
            raise Exception("Form field type not recognized.")

        if self.form_field_type in ('dropdown', 'radio'):
            field['options'] = [{'id': key, 'value': value} for key, value in self.options.items()]

        return field
