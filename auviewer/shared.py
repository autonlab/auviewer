"""Shared methods for the package."""

import pandas as pd
from pathlib import Path

# Creates an empty json file at the provided path (pathlib.Path object) if the
# file does not already exist.
def createEmptyJSONFile(path_obj):
    if not path_obj.exists():
        with path_obj.open(mode='x') as f:
            f.write("{\n\n}")

def annotationDataFrame(annotationModels):
    """Given a list of annotation models, returns a DataFrame in our standard format."""
    return pd.DataFrame(
        [[
            a.file.id,
            Path(a.file.path).name,
            a.user.id, a.user.email,
            a.user.first_name,
            a.user.last_name,
            a.pattern_set_id,
            a.pattern_id,
            a.series,
            a.left,
            a.right,
            a.top,
            a.bottom,
            a.label,
            a.created_at,
            f"{a.project_id}_{a.file.id}_{a.series}_{a.left}_{a.right}_{a.top}_{a.bottom}",
        ] for a in annotationModels],
        columns=['file_id', 'filename', 'user_id', 'user_email', 'user_firstname', 'user_lastname', 'pattern_set_id',
                 'pattern_id', 'series', 'left', 'right', 'top', 'bottom', 'label', 'created', 'pattern_identifier']
    )

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

def getProcFNFromOrigFN(fp):
    """Returns the processed filename (as Path object, which can be treated as string) from origina filename (as string or Path object)"""
    return Path(Path(fp).stem + '_processed.h5')

def patternDataFrame(patternModels):
    """Given a list of pattern models, returns a DataFrame in our standard format."""
    return pd.DataFrame(
            [[
                pattern.file.id,
                Path(pattern.file.path).name,
                pattern.series,
                pattern.left,
                pattern.right,
                pattern.top,
                pattern.bottom,
                pattern.label,
                f"{pattern.project_id}_{pattern.file.id}_{pattern.series}_{pattern.left}_{pattern.right}_{pattern.top}_{pattern.bottom}",
            ] for pattern in patternModels],
            columns=['file_id', 'filename', 'series', 'left', 'right', 'top', 'bottom', 'label', 'pattern_identifier']
        )