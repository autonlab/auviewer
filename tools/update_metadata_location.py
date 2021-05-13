import h5py as h5
import json
from pathlib import Path

# Directory containing files to be updated (will update all .h5 files)
targetDirectory = '.'

for p in [p for p in Path(targetDirectory).glob('*.h5') if p.is_file()]:

    print(f"{p}...", end=' ')

    f = h5.File(p, 'r+')

    # Check expected conditions
    fmp = True
    try:
        f.attrs['.meta']
    except:
        fmp = False

    if fmp:
        print("FILE META ALREADY PRESENT!")
        continue

    try:
        f['/.meta'].attrs['audata']
        f['/.meta'].attrs['data']
    except:
        print("AUDATA OR DATA META ATTR NOT FOUND!")
        continue

    audm = json.loads(f['/.meta'].attrs['audata'])

    audm['audata_pkg_version'] = '1.0.3' #audm['version']
    audm['audata_version'] = audm['data_version']

    del audm['version']
    del audm['data_version']

    dm = json.loads(f['/.meta'].attrs['data'])

    if 'title' in dm and dm['title'] is None:
        del dm['title']
    if 'author' in dm and dm['author'] is None:
        del dm['author']
    if 'organization' in dm and dm['organization'] is None:
        del dm['organization']

    dm['time_origin'] = dm['time']['origin']
    del dm['time']

    f.attrs['.meta'] = json.dumps({
        **audm,
        **dm
    })

    del f['.meta']

    f.close()

    print("Done.")
