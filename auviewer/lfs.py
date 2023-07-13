# File storing Labeling Function Pool

from snorkel.labeling import labeling_function



@labeling_function()
def SvO2_2min_mean_lowerbound(pig):
    if pig['SvO2_mean [2 min]'] >= 60:
        return SUFFICIENT
    else:
        return ABSTAIN

@labeling_function()
def SvO2_2min_mean_upperbound(pig):
    if pig['SvO2_mean [2 min]'] <= 65:
        return SUFFICIENT
    else:
        return ABSTAIN

@labeling_function()
def ART_5min_mean_upperbound(pig):
    if pig['ART_mean [5 min]'] <= 70:
        return SUFFICIENT
    else:
        return ABSTAIN

@labeling_function()
def ART_5min_mean_lowerbound(pig):
    if pig['ART_mean [5 min]'] >= 60:
        return SUFFICIENT
    else:
        return ABSTAIN

@labeling_function()
def ART_5min_mean_lowerbound(pig):
    if pig['ART_mean [5 min]'] >= 60:
        return SUFFICIENT
    else:
        return ABSTAIN