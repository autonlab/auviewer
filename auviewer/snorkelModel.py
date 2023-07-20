import pandas as pd 
from auviewer import lfs
import importlib
import numpy as np

from snorkel.labeling.model import LabelModel
from snorkel.labeling import PandasLFApplier
from datetime import datetime


# Read annotations from the doctors for sufficiency






def getAnnotationInvervals():
    ### The following is from Ryan's 02_featurization.ipynb
    df_annot = pd.read_csv("/Users/qingyang/desktop/AutonLab/resuscitation-project/for_sophia/sufficiency_annotations.csv")
    # Extract and add pig id as a column
    pig_ids = [file[:2] for file in df_annot['filename']]
    df_annot['pigID'] = pig_ids

    df_annot = df_annot.loc[df_annot['user_lastname'] == 'Gomez']
    df_annot['left'] = df_annot['left'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f").timestamp())
    df_annot['right'] = df_annot['right'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f").timestamp())
    pigid_intervals = {}
    for index, row in df_annot.iterrows():
        pigid = float(row['pigID'])
        if pigid not in pigid_intervals:
            pigid_intervals[pigid] = [(row['left'], row['right'])]
        else:
            pigid_intervals[pigid].append((row['left'], row['right']))

    return pigid_intervals


def runSnorkelModel(lfs_name_list):
    df_train = pd.read_csv("/Users/qingyang/desktop/AutonLab/resuscitation-project/for_sophia/statistics.csv")

    lfs_list = []
    importlib.reload(lfs)
    for lf_name in lfs_name_list:
        lf_function = getattr(lfs, lf_name, None)
        lfs_list.append(lf_function)

    # Apply the LFs to the unlabeled training data
    applier = PandasLFApplier(lfs_list)
    L_train = applier.apply(df_train)
    # L_train: label matrix, L[i, j] is the label that the jth labeling function output for the ith data point
    
    label_model = LabelModel(cardinality=2, verbose=True)
    label_model.fit(L_train, n_epochs=500, log_freq=50, seed=123)
    df_train["snorkel_label"] = label_model.predict(L=L_train, tie_break_policy="abstain")

    # if "normalized_t [min]" not in df_train:
    #     df_train.insert(loc = 1, column = "normalized_t [min]", value = df_train["timestamp"] - df_train["timestamp"][0])
    # df_train["normalized_t [min]"] = df_train["normalized_t [min]"] / 60

    pigid_intervals = getAnnotationInvervals()
    accu_dict = dict.fromkeys(range(1, 46), (0, 0))
    

    for i, row in df_train.iterrows():
        pigID = row["pigID"]
        intervals = pd.arrays.IntervalArray.from_tuples(pigid_intervals[pigID])
        trueSum, falseSum = accu_dict.get(pigID)
        if any(intervals.contains(row["timestamp"])) == row["snorkel_label"]:
            accu_dict[pigID] = (trueSum + 1, falseSum)
        else:
            accu_dict[pigID] = (trueSum, falseSum + 1)

    return accu_dict

