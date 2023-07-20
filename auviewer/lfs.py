# File storing Labeling Function Pool

from snorkel.labeling import labeling_function


# Define the label mappings for convenience
ABSTAIN = -1
INSUFFICIENT = 0
SUFFICIENT = 1




@labeling_function()
def ART_mean_higherbound(pig):
    if pig['ART_mean [5 min]'] <= 75:
        return SUFFICIENT
    else:
        return ABSTAIN

@labeling_function()
def ART_mean_lowerbound(pig):
    if pig['ART_mean [5 min]'] >= 60:
        return SUFFICIENT
    else:
        return ABSTAIN

@labeling_function()
def SvO2_mean_lowerbound(pig):
    if pig['SvO2_mean [2 min]'] >= 60:
        return SUFFICIENT
    else:
        return ABSTAIN

@labeling_function()
def SvO2_mean_lowerbound(pig):
    if pig['SvO2_mean [2 min]'] >= 60:
        return SUFFICIENT
    else:
        return ABSTAIN