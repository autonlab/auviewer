# Exception raised when file processing cannot proceed because the processed
# file already exists.
class ProcessedFileExists(Exception):
    pass