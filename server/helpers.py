import h5py as h5
from copy import copy

def gather_datasets_recursive(obj, path=[]):

    if isinstance(obj, h5.Dataset):
        return [(obj, path)]
    elif isinstance(obj, h5.File) or isinstance(obj, h5.Group):
        objects = []
        for i in obj:
            this_path = copy(path)
            this_path.append(i)
            objects.extend(gather_datasets_recursive(obj[i], this_path))
        return objects
    else:
        raise Exception("Unexpected object type in gather_datasets_recursive:", type(obj))