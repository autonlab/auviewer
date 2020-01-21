###########################################################################
# This is a code sample for using AUView as a module instead of a server. #
###########################################################################

from project import Project

# Load the conditionc project
project = Project('conditionc')

# Print a list of available processed files
print('Here is a list of files:\n\n', project.getProcessedFileList())

# Load a file in the project folder
file = project.loadProcessedFile('20190523_1053954_1173378.h5')

# Print out series names available in the file
print("\nHere is a list of series available:\n\n", file.getSeriesNames())

# Run anomaly detection
anomalies = file.detectAnomalies(
    series = 'numerics/HR.HR/data',
    thresholdlow=58,
    thresholdhigh=110,
    duration=10,
    persistence=0.70,
    maxgap=1800
)

print('\nHere is a list of anomalies detected.\n')
for a in anomalies:
    print(a)