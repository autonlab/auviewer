###########################################################################
# This is a code sample for using AUView as a module instead of a server. #
###########################################################################

import sys, os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]), 'server'))

from ..server.project import Project

def main():
    # Load the conditionc project
    project = Project('ConditionC')

    # Print a list of available processed files
    print('Here is a list of files:\n\n', project.getProcessedFileList())

    # Load a file in the project folder
    file = project.loadProcessedFile('20190805_1008278_1978248.h5')

    # Print out series names available in the file
    print("\nHere is a list of series available:\n\n", file.getSeriesNames(), "\n")

    # Get a series
    spo2Series = file.getSeries('numerics/SpO₂.SpO₂/data')

    # Tell system to read the series data into memory from the file
    spo2Series.pullRawDataIntoMemory()
    print()

    # Now you have rawTimes and rawValues Numpy arrays available to work with
    print('rawTimes', type(spo2Series.rawTimes), spo2Series.rawTimes.shape)
    print(spo2Series.rawTimes, "\n")
    print('rawValues', type(spo2Series.rawValues), spo2Series.rawValues.shape)
    print(spo2Series.rawValues, "\n")

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

if __name__ == '__main__':
    main()
