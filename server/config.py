# This file holds configuration parameters for the medview application.

# A root directory from which the web application is served. Should begin with a
# slash and end without a slask (in other words, end with a directory name).
rootDir = '/auv'

# Max number of data points to transmit for a given view
M = 3000

# The number to multiply by numDownsamples each time in building downsample
# levels. For example, if M=3000 and stepMultipler=2, the first downsample
# is 3K intervals, the second 6K, the third 12K, and so forth.
stepMultiplier = 2

# Original patient data files (which should be preserved and unaltered) go here.
# originalFilesDir = '../data/originals/'
# originalFilesDir = '/zfsauton/data/public/vleonard/'
originalFilesDir = '/home/scratch/gwelter/meddata/originals/'

# Processed (i.e. downsampled) patient data files go here.
# processedFilesDir = '../data/processed/'
processedFilesDir = '/home/scratch/gwelter/meddata/processed/'