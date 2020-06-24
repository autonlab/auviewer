# ATW: TODO: Untested after audata transition. This will be re-evaluated after the
# move to bokeh when realtime will be re-enabled.
import sys, os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]), 'server'))

import numpy as np
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import audata

from ..server.file import File

# Configurable variables
ORIGINALS_FOLDER_NAME = 'originals'
PROCESSED_FOLDER_NAME = 'processed'

# This flag indicates new file(s) have been added and so to rebuild
Rebuild = False

class Handler(FileSystemEventHandler):

    @staticmethod
    def on_created(event):

        global Rebuild, source_path, original_filename, processed_filename

        if event.is_directory:
            return

        if event.src_path == os.path.join(source_path, original_filename) or event.src_path == os.path.join(source_path, processed_filename):
            print("Suppressing watch event:", event.src_path)
            return
        else:
            print("Detected new file:", event.src_path)

        global Rebuild
        Rebuild = True

def rebuild(source_path, project_target_path, original_filename, processed_filename):

    print("Rebuilding.")

    # Wait a beat in case multiple files being moved into directory quickly.
    time.sleep(1)

    # Get sorted list of h5 files in the directory
    files_list = sorted([filename for filename in os.listdir(source_path) if filename.endswith('.h5')])

    # Set the rebuild flag to false. We do this immediately after retrieving the
    # files list purposefully.
    global Rebuild
    Rebuild = False

    if len(files_list) == 0:
        return

    # Holds the contents to be written to the new original file
    datasets = {}

    # Iterate through all partial files# Iterate through all partial files
    for sfn in files_list:

        # Open partial file as read-only
        with audata.File.open(os.path.join(source_path, sfn), return_datetimes=False) as sf:

            # Iteratee through all datasets in the partial file
            for (ds, path) in sf.recurse():

                # Prepare the path string (path itself is a list)
                path_string = '/' + '/'.join(path)

                # Add the data to the new original datasets
                if path_string in datasets:
                    datasets[path_string] = np.concatenate((datasets[path_string], ds[()]))
                else:
                    datasets[path_string] = ds[()]

    # Once all datasets are prepared, write them to the new original file.
    # For now, put the file in the source path; we'll move it when ready.
    # with h5.File(os.path.join(project_target_path, ORIGINALS_FOLDER_NAME, original_filename), 'w') as f:
    with audata.File.new(os.path.join(source_path, original_filename), overwrite=True, return_datetimes=False) as f:
        for path in datasets:
            f[path] = datasets[path]

    # Now, create downsamples & generate the processed file. For now, put the
    # processed file in the source path; we'll move it when ready.
    File(
        projparent=None,
        orig_filename=original_filename,
        proc_filename=processed_filename,
        orig_dir=source_path,
        proc_dir=source_path
    ).__del__()

    print('Finished rebuilding.')

    # Move the newly-generated files to their final destinations. We move the
    # processed file first since the original file replace is what will trigger
    # the viewer backend to reload the file.
    os.replace(
        os.path.join(source_path, processed_filename),
        os.path.join(project_target_path, PROCESSED_FOLDER_NAME, processed_filename)
    )
    os.replace(
        os.path.join(source_path, original_filename),
        os.path.join(project_target_path, ORIGINALS_FOLDER_NAME, original_filename)
    )

    print('Moved files to final destinations.')

def main():
    # We expect three command-line arguments
    if len(sys.argv) != 4:
        print("Three command-line arguments expected:")
        print("- Source path (where to watch for files)")
        print("- Project target path (where to put newly generated original & processed files)")
        print("- Output file name (name of the \"original\" file to be generated; processed file name will be derived therefrom)")
        quit()

    # Source directory (where to watch for files)
    source_path = sys.argv[1]

    # Project directory (where to put newly generated original & processed files)
    project_target_path = sys.argv[2]

    # Output filename for original file
    original_filename = sys.argv[3]

    # Processed filename
    processed_filename = os.path.splitext(original_filename)[0] + '_processed.h5'

    # Begin watching for new files
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, source_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            if Rebuild:
                rebuild(source_path, project_target_path, original_filename, processed_filename)

    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == '__main__':
    main()
