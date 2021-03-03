from abc import ABC, abstractmethod
from typing import AnyStr, List, Dict, Optional, Union

class Featurizer(ABC):

    def __init__(self, files: Union[str, List[str]], series: Union[str, List[str], None]):

        # If a string was provided as the files param (i.e. referencing a single file), convert it to a list
        if isinstance(files, str):
            files = [files]

        # If a string was provided as the series param (i.e. referencing a single series), convert it to a list
        if isinstance(series, str):
            series = [series]

        # Set files & series as instance properties
        self.files = files
        self.series = series

    @abstractmethod
    def get_dialog_template(self):
        """

        :return:
        """
        raise NotImplementedError("Error! Required featurizer method not implemented.")