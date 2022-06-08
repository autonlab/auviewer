from asyncore import write
from os import listdir
from os.path import isfile, join
import pandas as pd
import datetime
from random import randrange
import utils
import csv
import audata as aud
import pytz
import time



def randomTime(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + datetime.timedelta(seconds=random_second)

path = "/home/cindy/Documents/github/auviewer/assets/auvdata/projects/afibsample/originals"
segLength = 10
onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
print(onlyfiles)
seriesOfInterest = utils.HR_SERIES
repeat = 10
print(len(onlyfiles))
for filename in onlyfiles:
    filepath = path+"/"+filename
    f = aud.File.open(filepath)
    print("success")


    filename = (filename.split("."))[0]
    newfilename = filename + "_10s_segments"
    fin_id = (((filename.split('_'))[2]).split("."))[0]
    print(fin_id)


    fileStartTime = f[seriesOfInterest][0]['time'].item().to_pydatetime()
    fileEndTime = f[seriesOfInterest][-1]['time'].item().to_pydatetime()
    if(fileStartTime is None or fileEndTime is None):
        print("no time")== None
        continue
    fileStartTime, fileEndTime = fileStartTime.replace(tzinfo=pytz.UTC), fileEndTime.replace(tzinfo=pytz.UTC)

    print("got time")




    newpath = "./" + newfilename + ".csv"
    newfile = open(newpath, 'w')
    writer = csv.writer(newfile)

    writer.writerow(['start', 'end', 'fin_id'])
    for i in range(0, repeat):
        randstart = randomTime(fileStartTime, fileEndTime)
        randend = randstart + datetime.timedelta(0,10)
        writer.writerow([randstart, randend, fin_id])
    
    print("shutting down")
    time.sleep(1)

    newfile.close()
        


