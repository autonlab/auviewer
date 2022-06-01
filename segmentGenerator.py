from asyncore import write
from os import listdir
from os.path import isfile, join
import pandas as pd
import datetime
from random import randrange
import csv

def randomTime(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + datetime.timedelta(seconds=random_second)

path = "./assets/auvdata/projects/afibsample/originals"
segLength = 10
onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
print(onlyfiles)
for filename in onlyfiles:
    filename = (filename.split("."))[0]
    filepath = path+"/"+filename
    newfilename = filename + "_10s_segments"
    fin_id = (((filename.split('_'))[2]).split("."))[0]
    print(fin_id)
    start = "2018-05-16 22:40:00"
    end = "2018-05-23 12:54:00"
    starttime = datetime.datetime.fromisoformat(start)
    endatetimeime = datetime.datetime.fromisoformat(end)
    newpath = "./" + newfilename + ".csv"
    newfile = open(newpath, 'w')
    writer = csv.writer(newfile)

    writer.writerow(['start', 'end', 'fin_id'])
    for i in range(0, 10):
        randstart = randomTime(starttime, endatetimeime)
        randend = randstart + datetime.timedelta(0,10)
        writer.writerow([randstart, randend, fin_id])
        
    newfile.close()
        


