# This file holds configuration parameters for the medview application.

# Max number of data points to transmit for a given view
M = 3000

# The number to multiply by numDownsamples each time in building downsample
# levels. For example, if M=3000 and stepMultipler=2, the first downsample
# is 3K intervals, the second 6K, the third 12K, and so forth.
stepMultiplier = 2

# Original patient data files (which should be preserved and unaltered) go here.
# originalFilesDir = '../data/originals/'
originalFilesDir = '/zfsauton/data/public/vleonard/'

# Processed (i.e. downsampled) patient data files go here.
processedFilesDir = '../data/processed/'

# Scratch directory for use during development (storing pickle files here currently).
scratchFilesDir = '../data/scratch/'
