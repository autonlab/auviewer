"""Shared methods for the package."""

from pathlib import Path

# Creates an empty json file at the provided path (pathlib.Path object) if the
# file does not already exist.
def createEmptyJSONFile(path_obj):
    if not path_obj.exists():
        with path_obj.open(mode='x') as f:
            f.write("{\n\n}")

# Given an Annotation or Pattern model, returns a list formatted for API output.
# A second parameter, related, may be provided in which case the function will
# output a representation for both items in a single list. For example, you may
# provide an annotation and the pattern it annotates, or a pattern and the
# annotation that annotates it.
# TODO: Review whether both cases will be used.
def annotationOrPatternOutput(primary, related=None):
    output = []
    for a in [primary, related]:
        if a is not None:
            output = output + [
                a.id,
                a.file_id,
                Path(a.file.path).name,
                a.series,
                a.left,
                a.right,
                a.top,
                a.bottom,
                a.label,
                a.pattern_id if hasattr(a, 'pattern_id') else None
            ]
    return output