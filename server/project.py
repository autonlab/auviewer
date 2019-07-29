import config
from file import File
import os

class Project:

    def __init__(self):

        # Holds references to the files that belong to the project
        self.files = []

    def getUnprocessedFiles(self):

        response = []

        for fn in os.listdir(config.originalFilesDir):
            if fn.endswith(".h5") and fn == "test_wave_20190626.h5":
                response.append([fn, config.originalFilesDir])

        return response

    def processUnprocessedFiles(self):

        for f in self.getUnprocessedFiles():
            file = File(f[0], f[1])
            file.processAndStore()
            self.files.append(file)