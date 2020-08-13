"""Shared methods for the package."""

# Creates an empty json file at the provided path (pathlib.Path object) if the
# file does not already exist.
def createEmptyJSONFile(path_obj):
    if not path_obj.exists():
        with path_obj.open(mode='x') as f:
            f.write("{\n\n}")